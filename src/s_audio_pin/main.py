import argparse
import logging
import os
import shutil
import signal
import socket
import subprocess
import sys
import threading
import time
import urllib.parse
import webbrowser
from pathlib import Path
from typing import Optional

import uvicorn

from . import APP_ID, __version__
from .config.settings import get_config_dir
from .server.app import app
from .window import (
    find_system_gtk_python,
    has_inprocess_gtk_webkit,
    request_gtk_quit,
    run_gtk_window,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("s_audio_pin")

HOST = "127.0.0.1"


def _pick_free_port(host: str = HOST) -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, 0))
        return int(s.getsockname()[1])


def _wait_for_server_ready(
    host: str,
    port: int,
    server: uvicorn.Server,
    server_thread: threading.Thread,
    timeout_secs: float = 5.0,
) -> bool:
    deadline = time.monotonic() + timeout_secs
    while time.monotonic() < deadline:
        if not server_thread.is_alive():
            return False
        if server.started:
            try:
                with socket.create_connection((host, port), timeout=0.2):
                    return True
            except OSError:
                pass
        time.sleep(0.05)
    return False


def _launch_chromium_fallback(url: str) -> Optional[subprocess.Popen]:
    chrome_profile = get_config_dir() / "browser-profile"
    chrome_profile.mkdir(parents=True, exist_ok=True)

    candidates = [
        "google-chrome",
        "google-chrome-stable",
        "chromium",
        "chromium-browser",
        "brave-browser",
        "microsoft-edge",
    ]

    for browser in candidates:
        browser_bin = shutil.which(browser)
        if browser_bin:
            cmd = [
                browser_bin,
                f"--app={url}",
                f"--user-data-dir={chrome_profile}",
                "--window-size=1080,740",
                f"--class={APP_ID}",
                f"--name={APP_ID}",
                "--no-first-run",
                "--no-default-browser-check",
            ]
            try:
                logger.info("Launching standalone browser window via %s...", browser)
                return subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception as e:
                logger.warning("Could not launch %s app mode: %s", browser, e)

    return None


def _parse_args(argv: Optional[list] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="s-audio-pin",
        description="S_Audio_Pin_Linux — Audio Process Monitor & Selective Recorder",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument(
        "--port",
        type=int,
        default=0,
        help="Port for local API/UI server (default: 0 for automatic free port)",
    )
    parser.add_argument(
        "--no-window",
        action="store_true",
        help="Run backend server without opening a GUI window",
    )
    parser.add_argument(
        "--browser",
        action="store_true",
        help="Open UI in Chromium/system browser instead of native GTK4/WebKitGTK window",
    )
    return parser.parse_args(argv)


def main(argv: Optional[list] = None) -> int:
    args = _parse_args(argv)
    import secrets

    port = args.port if args.port > 0 else _pick_free_port(HOST)
    api_token = secrets.token_urlsafe(24)
    base_url = f"http://{HOST}:{port}"
    ui_url = f"{base_url}/?token={urllib.parse.quote(api_token)}"
    status_url = f"{base_url}/api/record/status"
    icon_dir = str(Path(__file__).resolve().parent / "ui" / "img")

    app.state.api_token = api_token
    stop_event = threading.Event()
    window_proc: Optional[subprocess.Popen] = None

    config = uvicorn.Config(
        app,
        host=HOST,
        port=port,
        log_level="info",
        access_log=False,
    )
    server = uvicorn.Server(config)
    server.install_signal_handlers = lambda: None

    def _shutdown_all():
        stop_event.set()
        server.should_exit = True
        request_gtk_quit()
        if window_proc is not None and window_proc.poll() is None:
            try:
                window_proc.terminate()
            except Exception:
                pass

    app.state.shutdown_callback = _shutdown_all

    def _on_os_signal(_signum, _frame):
        _shutdown_all()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            signal.signal(sig, _on_os_signal)
        except Exception:
            pass

    logger.info("=" * 60)
    logger.info("   S_Audio_Pin_Linux v%s — Audio Monitor & Selective Recorder", __version__)
    logger.info("   Local UI server: %s", base_url)
    logger.info("=" * 60)

    server_thread = threading.Thread(target=server.run, daemon=True)
    server_thread.start()

    try:
        if not _wait_for_server_ready(HOST, port, server, server_thread, timeout_secs=5.0):
            logger.error("Local server failed to start on %s:%d", HOST, port)
            return 1

        if args.no_window:
            logger.info("Running in headless mode (--no-window). UI URL: %s", ui_url)
            while not stop_event.is_set() and server_thread.is_alive():
                stop_event.wait(timeout=0.5)
            return 0

        if not args.browser and has_inprocess_gtk_webkit():
            logger.info("Launching native GTK4 + WebKitGTK window (in-process)...")
            run_gtk_window(
                url=ui_url,
                title="S_Audio_Pin",
                app_id=APP_ID,
                icon_path=icon_dir,
                status_url=status_url,
                token=api_token,
            )
            return 0

        if not args.browser:
            sys_gtk_py = find_system_gtk_python(require_webkit=True)
            if sys_gtk_py:
                logger.info("Launching native GTK4 + WebKitGTK window via %s...", sys_gtk_py)
                window_script = str(Path(__file__).resolve().parent / "window.py")
                window_proc = subprocess.Popen(
                    [
                        sys_gtk_py,
                        window_script,
                        "--url",
                        ui_url,
                        "--title",
                        "S_Audio_Pin",
                        "--app-id",
                        APP_ID,
                        "--icon",
                        icon_dir,
                        "--status-url",
                        status_url,
                        "--token",
                        api_token,
                    ]
                )
                window_proc.wait()
                return 0

        # Browser fallback
        started_at = time.monotonic()
        window_proc = _launch_chromium_fallback(ui_url)
        if window_proc is not None:
            exit_code = window_proc.wait()
            # If Chromium delegated to an existing browser process and returned immediately,
            # keep the backend alive until /api/shutdown or SIGINT/SIGTERM.
            if exit_code == 0 and (time.monotonic() - started_at) < 2.0:
                logger.info("Browser handed off window to existing session; waiting for shutdown signal...")
                while not stop_event.is_set() and server_thread.is_alive():
                    stop_event.wait(timeout=0.5)
            return 0

        logger.info("Opening UI in default web browser: %s", ui_url)
        webbrowser.open(ui_url)
        while not stop_event.is_set() and server_thread.is_alive():
            stop_event.wait(timeout=0.5)
        return 0
    finally:
        stop_event.set()
        server.should_exit = True
        if window_proc is not None and window_proc.poll() is None:
            try:
                window_proc.terminate()
                window_proc.wait(timeout=2.0)
            except Exception:
                try:
                    window_proc.kill()
                except Exception:
                    pass
        if server_thread.is_alive():
            server_thread.join(timeout=5.0)


if __name__ == "__main__":
    raise SystemExit(main())

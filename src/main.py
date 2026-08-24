import sys
import os
import time
import shutil
import logging
import urllib.request
import subprocess
import webbrowser
from pathlib import Path
import uvicorn

# Set up root logging format
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("s_audio_pin")

HOST = "127.0.0.1"
PORT = 8765
APP_URL = f"http://{HOST}:{PORT}"


def is_server_running() -> bool:
    """Checks if S_Audio_Pin server is already responding on the expected port."""
    try:
        req = urllib.request.Request(f"{APP_URL}/api/config", method="GET")
        with urllib.request.urlopen(req, timeout=0.4) as response:
            return response.status == 200
    except Exception:
        return False


def launch_app_window(url: str):
    """
    Opens the application in a borderless, dedicated standalone app window (App Mode),
    falling back to standard browser if no Chromium engine is available.
    """
    chrome_profile = Path.home() / ".config" / "s_audio_pin" / "app_profile"
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
                "--window-size=1080,780",
                "--class=s_audio_pin",
                "--name=s_audio_pin",
                "--no-first-run",
                "--no-default-browser-check",
            ]
            try:
                logger.info(f"Launching standalone app window via {browser}...")
                subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return
            except Exception as e:
                logger.warning(f"Could not launch {browser} app mode: {e}")

    # Fallback to standard web browser
    logger.info("Opening UI in default browser...")
    webbrowser.open(url)


def main():
    # 1. If server is already running in background, just open the window and exit
    if is_server_running():
        logger.info("S_Audio_Pin background server is already active. Launching window...")
        launch_app_window(APP_URL)
        sys.exit(0)

    logger.info("=" * 60)
    logger.info("   🎙️  S_Audio_Pin_Linux — Audio Monitor & Selective Recorder")
    logger.info(f"   🌐 UI available at: {APP_URL}")
    logger.info("=" * 60)

    # 2. Launch App-Mode window after short delay to let server bind
    def _delayed_launch():
        time.sleep(0.8)
        launch_app_window(APP_URL)

    import threading
    threading.Thread(target=_delayed_launch, daemon=True).start()

    # 3. Start server
    uvicorn.run(
        "src.server.app:app",
        host=HOST,
        port=PORT,
        log_level="info",
        access_log=True,
    )


if __name__ == "__main__":
    main()

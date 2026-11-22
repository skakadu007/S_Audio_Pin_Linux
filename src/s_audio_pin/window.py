"""
Native GTK4 + WebKitGTK 6.0 window shell and folder-picker portal helper.

IMPORTANT: This module intentionally imports ONLY Python standard library modules
plus optional PyGObject (`gi`), so it can be executed directly by system Python
(`/usr/bin/python3`) even when the backend server runs inside an isolated `.venv`.
"""

import argparse
import json
import logging
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import urllib.request
from pathlib import Path
from typing import Optional

APP_ID = "io.github.skakadu007.SAudioPin"
logger = logging.getLogger("s_audio_pin.window")

_ACTIVE_LOCK = threading.Lock()
_ACTIVE_APP = None
_ACTIVE_WIN = None


def has_inprocess_gtk_webkit() -> bool:
    """Returns True if GTK 4.0 and WebKit 6.0 are importable in the current Python interpreter."""
    try:
        import gi

        gi.require_version("Gtk", "4.0")
        gi.require_version("WebKit", "6.0")
        from gi.repository import Gtk, WebKit  # noqa: F401

        return True
    except Exception:
        return False


def has_inprocess_gtk() -> bool:
    """Returns True if GTK 4.0 is importable in the current Python interpreter."""
    try:
        import gi

        gi.require_version("Gtk", "4.0")
        from gi.repository import Gtk  # noqa: F401

        return True
    except Exception:
        return False


def find_system_gtk_python(require_webkit: bool = True) -> Optional[str]:
    """
    Searches for a system Python interpreter that has PyGObject + GTK 4.0
    (and optionally WebKit 6.0) installed.
    """
    candidates = []
    for cand in ("/usr/bin/python3", shutil.which("python3")):
        if cand and cand not in candidates and os.path.exists(cand):
            candidates.append(cand)

    check_code = (
        "import gi; gi.require_version('Gtk', '4.0'); "
        + ("gi.require_version('WebKit', '6.0'); " if require_webkit else "")
        + "from gi.repository import Gtk"
        + (", WebKit" if require_webkit else "")
    )

    for py in candidates:
        try:
            res = subprocess.run(
                [py, "-c", check_code],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=3.0,
            )
            if res.returncode == 0:
                return py
        except Exception:
            continue
    return None


def request_gtk_quit() -> None:
    """Cleanly closes the active in-process GTK application if one is running."""
    with _ACTIVE_LOCK:
        app = _ACTIVE_APP
    if app is not None:
        try:
            from gi.repository import GLib

            GLib.idle_add(app.quit)
        except Exception:
            pass


def _is_recording_active(status_url: Optional[str], token: Optional[str]) -> bool:
    if not status_url:
        return False
    try:
        headers = {}
        if token:
            headers["X-API-Token"] = token
        req = urllib.request.Request(status_url, headers=headers, method="GET")
        with urllib.request.urlopen(req, timeout=0.35) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                return bool(data.get("is_recording"))
    except Exception:
        pass
    return False


def _setup_icon_theme(app_id: str, icon_path: Optional[str]) -> Optional[tempfile.TemporaryDirectory]:
    if not icon_path:
        return None
    src = Path(icon_path)
    if not src.exists():
        return None

    from gi.repository import Gdk, Gtk

    display = Gdk.Display.get_default()
    if display is None:
        return None

    theme = Gtk.IconTheme.get_for_display(display)
    if theme.has_icon(app_id):
        return None

    if src.is_dir():
        theme.add_search_path(str(src))
        if theme.has_icon(app_id):
            return None
        svg_file = src / "icon.svg"
        png_file = src / "icon_256.png"
    else:
        svg_file = src if src.suffix.lower() == ".svg" else None
        png_file = src if src.suffix.lower() == ".png" else None

    tmp_dir = tempfile.TemporaryDirectory(prefix="s_audio_pin_icons_")
    base = Path(tmp_dir.name)
    if svg_file and svg_file.exists():
        target_dir = base / "hicolor" / "scalable" / "apps"
        target_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(svg_file, target_dir / f"{app_id}.svg")
    if png_file and png_file.exists():
        target_dir = base / "hicolor" / "256x256" / "apps"
        target_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(png_file, target_dir / f"{app_id}.png")

    theme.add_search_path(str(base / "hicolor"))
    return tmp_dir


def _install_glib_signal_quit(app) -> None:
    from gi.repository import GLib

    def _on_signal(*_args):
        app.quit()
        return GLib.SOURCE_REMOVE if hasattr(GLib, "SOURCE_REMOVE") else False

    try:
        from gi.repository import GLibUnix

        for sig in (signal.SIGTERM, signal.SIGUSR1):
            GLibUnix.signal_add(GLib.PRIORITY_DEFAULT, sig, _on_signal)
        return
    except Exception:
        pass

    if hasattr(GLib, "unix_signal_add"):
        for sig in (signal.SIGTERM, signal.SIGUSR1):
            try:
                GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, sig, _on_signal)
            except Exception:
                pass


def run_gtk_window(
    url: str,
    title: str = "S_Audio_Pin",
    app_id: str = APP_ID,
    icon_path: Optional[str] = None,
    status_url: Optional[str] = None,
    token: Optional[str] = None,
) -> int:
    """
    Launches the native GTK4 + WebKitGTK 6.0 application window and blocks until closed.
    """
    import gi

    gi.require_version("Gtk", "4.0")
    gi.require_version("WebKit", "6.0")
    from gi.repository import Gdk, Gio, GLib, Gtk, WebKit

    GLib.set_prgname(app_id)
    GLib.set_application_name(title)

    app = Gtk.Application(application_id=app_id, flags=Gio.ApplicationFlags.NON_UNIQUE)
    icon_tmpdir: Optional[tempfile.TemporaryDirectory] = None
    state = {"force_close": False}

    def on_activate(gtk_app):
        nonlocal icon_tmpdir
        with _ACTIVE_LOCK:
            global _ACTIVE_APP, _ACTIVE_WIN
            _ACTIVE_APP = gtk_app
            if _ACTIVE_WIN is not None:
                _ACTIVE_WIN.present()
                return

        gtk_settings = Gtk.Settings.get_default()
        if gtk_settings is not None:
            gtk_settings.set_property("gtk-application-prefer-dark-theme", True)

        icon_tmpdir = _setup_icon_theme(app_id, icon_path)

        win = Gtk.ApplicationWindow(application=gtk_app, title=title)
        win.set_default_size(1080, 740)
        win.set_size_request(760, 560)
        win.set_icon_name(app_id)

        with _ACTIVE_LOCK:
            _ACTIVE_WIN = win

        webview = WebKit.WebView()
        rgba = Gdk.RGBA()
        if rgba.parse("#0c0d12"):
            webview.set_background_color(rgba)

        wk_settings = webview.get_settings()
        if wk_settings is not None:
            wk_settings.set_enable_smooth_scrolling(True)
            wk_settings.set_enable_javascript(True)

        webview.load_uri(url)
        win.set_child(webview)

        def on_close_request(window):
            if state["force_close"]:
                return False
            if _is_recording_active(status_url, token):
                dialog = Gtk.AlertDialog(
                    message="Запис ще триває",
                    detail="Зупинити поточний запис, зберегти аудіо та вийти з програми?",
                )
                dialog.set_buttons(["Скасувати", "Зберегти і вийти"])
                dialog.set_cancel_button(0)
                dialog.set_default_button(1)

                def on_choice(d, res):
                    try:
                        choice = d.choose_finish(res)
                    except Exception:
                        choice = 0
                    if choice == 1:
                        state["force_close"] = True
                        window.close()

                dialog.choose(window, None, on_choice)
                return True
            return False

        win.connect("close-request", on_close_request)
        win.present()

    _install_glib_signal_quit(app)
    app.connect("activate", on_activate)

    try:
        return app.run(None)
    finally:
        with _ACTIVE_LOCK:
            _ACTIVE_APP = None
            _ACTIVE_WIN = None
        if icon_tmpdir is not None:
            try:
                icon_tmpdir.cleanup()
            except Exception:
                pass


def _pick_folder_gtk_non_unique(initial_dir: Optional[str] = None) -> Optional[str]:
    import gi

    gi.require_version("Gtk", "4.0")
    from gi.repository import Gio, Gtk

    chosen = {"path": None}
    app = Gtk.Application(flags=Gio.ApplicationFlags.NON_UNIQUE)

    def on_activate(gtk_app):
        gtk_app.hold()
        dialog = Gtk.FileDialog()
        dialog.set_title("Оберіть папку для збереження записів")
        if initial_dir and Path(initial_dir).expanduser().exists():
            dialog.set_initial_folder(Gio.File.new_for_path(str(Path(initial_dir).expanduser())))

        def on_done(d, res):
            try:
                folder = d.select_folder_finish(res)
                if folder is not None:
                    chosen["path"] = folder.get_path()
            except Exception:
                pass
            finally:
                gtk_app.release()
                gtk_app.quit()

        dialog.select_folder(None, None, on_done)

    app.connect("activate", on_activate)
    app.run(None)
    return chosen["path"]


def pick_folder_dialog(initial_dir: Optional[str] = None) -> Optional[str]:
    """
    Opens a native directory chooser (Gtk.FileDialog / XDG Portal when available,
    falling back to zenity or kdialog). Returns selected path or None if cancelled.
    """
    with _ACTIVE_LOCK:
        active_win = _ACTIVE_WIN

    # 1. In-process active GTK4 window
    if active_win is not None and has_inprocess_gtk():
        from gi.repository import Gio, GLib, Gtk

        done = threading.Event()
        result = {"path": None}

        def _show():
            dialog = Gtk.FileDialog()
            dialog.set_title("Оберіть папку для збереження записів")
            if initial_dir and Path(initial_dir).expanduser().exists():
                dialog.set_initial_folder(Gio.File.new_for_path(str(Path(initial_dir).expanduser())))

            def _on_done(d, res):
                try:
                    folder = d.select_folder_finish(res)
                    if folder is not None:
                        result["path"] = folder.get_path()
                except Exception:
                    pass
                finally:
                    done.set()

            dialog.select_folder(active_win, None, _on_done)
            return False

        GLib.idle_add(_show)
        done.wait(timeout=180.0)
        return result["path"]

    # 2. In-process GTK4 without active window (headless or tests)
    if has_inprocess_gtk():
        return _pick_folder_gtk_non_unique(initial_dir)

    # 3. Subprocess using system Python + GTK4 (NON_UNIQUE so it won't collide with main window)
    sys_py = find_system_gtk_python(require_webkit=False)
    if sys_py:
        cmd = [sys_py, str(Path(__file__).resolve()), "--pick-folder"]
        if initial_dir:
            cmd.extend(["--initial-dir", str(initial_dir)])
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=180.0)
            if res.returncode == 0:
                selected = res.stdout.strip()
                return selected or None
        except Exception as e:
            logger.debug("System GTK folder picker subprocess failed: %s", e)

    # 4. Fallback to zenity / kdialog
    zenity_bin = shutil.which("zenity")
    if zenity_bin:
        cmd = [zenity_bin, "--file-selection", "--directory", "--title=Оберіть папку для записів"]
        if initial_dir and Path(initial_dir).expanduser().exists():
            cmd.append(f"--filename={Path(initial_dir).expanduser()}/")
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=180.0)
            if res.returncode == 0:
                selected = res.stdout.strip()
                return selected or None
        except Exception:
            pass

    kdialog_bin = shutil.which("kdialog")
    if kdialog_bin:
        start_dir = str(Path(initial_dir).expanduser()) if initial_dir else str(Path.home())
        try:
            res = subprocess.run(
                [kdialog_bin, "--getexistingdirectory", start_dir],
                capture_output=True,
                text=True,
                timeout=180.0,
            )
            if res.returncode == 0:
                selected = res.stdout.strip()
                return selected or None
        except Exception:
            pass

    return None


def _parse_args(argv: Optional[list] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="s-audio-pin-window",
        description="S_Audio_Pin native GTK4 + WebKitGTK window & folder picker",
    )
    parser.add_argument("--url", help="URL to open inside the WebKitGTK window")
    parser.add_argument("--title", default="S_Audio_Pin", help="Window title")
    parser.add_argument("--app-id", default=APP_ID, help="GTK/Wayland application ID")
    parser.add_argument("--icon", default=None, help="Path to application icon or icon dir")
    parser.add_argument("--status-url", default=None, help="Recording status endpoint URL")
    parser.add_argument("--token", default=None, help="API token for status checks")
    parser.add_argument(
        "--pick-folder",
        action="store_true",
        help="Open native directory selection dialog and print selected path to stdout",
    )
    parser.add_argument("--initial-dir", default=None, help="Initial directory for folder picker")
    return parser.parse_args(argv)


def main(argv: Optional[list] = None) -> int:
    args = _parse_args(argv)
    if args.pick_folder:
        selected = _pick_folder_gtk_non_unique(args.initial_dir)
        if selected:
            print(selected)
        return 0

    if not args.url:
        print("Error: --url or --pick-folder is required.", file=sys.stderr)
        return 2

    return run_gtk_window(
        url=args.url,
        title=args.title,
        app_id=args.app_id,
        icon_path=args.icon,
        status_url=args.status_url,
        token=args.token,
    )


if __name__ == "__main__":
    raise SystemExit(main())

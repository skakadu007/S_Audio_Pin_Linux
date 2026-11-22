import os
import re
from typing import Dict, Any, Optional, Tuple


GENERIC_BINARIES = {
    "python",
    "python3",
    "java",
    "node",
    "electron",
    "wine",
    "wine64-preloader",
    "flatpak-spawn",
}

GENERIC_DISPLAY_NAMES = {
    "unknown application",
    "невідома програма",
    "playback stream",
    "audio stream",
    "python",
    "python3",
    "java",
    "node",
    "electron",
    "wine",
}


def _slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9._-]+", "_", value.strip().lower()).strip("_")


def clean_app_display_name(name: str, process_name: Optional[str] = None) -> str:
    """
    Cleans up noisy Linux application names into friendly display titles.
    """
    if not name or name == "Unknown Application":
        if process_name:
            name = os.path.basename(process_name)
        else:
            return "Невідома програма"

    name_mappings = {
        "viberpc": "Viber",
        "viber": "Viber",
        "spotify": "Spotify",
        "firefox": "Firefox",
        "google-chrome": "Google Chrome",
        "chromium": "Chromium",
        "chromium-browser": "Chromium",
        "brave-browser": "Brave",
        "telegram-desktop": "Telegram",
        "telegram": "Telegram",
        "discord": "Discord",
        "vlc": "VLC Media Player",
        "obs": "OBS Studio",
        "code": "Visual Studio Code",
        "steam": "Steam",
    }

    lower_name = name.lower()
    if lower_name in name_mappings:
        return name_mappings[lower_name]

    if lower_name.startswith("alsa plug-in [") and lower_name.endswith("]"):
        inner = lower_name[14:-1].strip()
        return name_mappings.get(inner, inner.capitalize())

    # Replace dashes/underscores if it looks like a binary name
    if name.islower() and ("_" in name or "-" in name):
        name = name.replace("_", " ").replace("-", " ").title()

    return name


def extract_process_info(proplist: Dict[str, Any]) -> Tuple[str, Optional[str], Optional[int], Optional[str]]:
    """
    Extracts (display_name, process_name, pid, icon_name) from PulseAudio/PipeWire proplist.
    Does not inspect /proc so it works reliably inside Flatpak PID namespaces.
    """
    pid: Optional[int] = None
    pid_str = proplist.get("application.process.id")
    if pid_str is not None:
        try:
            pid = int(pid_str)
        except (ValueError, TypeError):
            pid = None

    raw_binary: Optional[str] = proplist.get("application.process.binary")
    process_name: Optional[str] = os.path.basename(raw_binary) if raw_binary else None

    raw_name: str = (
        proplist.get("application.name")
        or process_name
        or proplist.get("media.name")
        or proplist.get("window.name")
        or "Unknown Application"
    )
    icon_name: Optional[str] = (
        proplist.get("application.icon_name")
        or process_name
        or proplist.get("application.name")
    )

    if icon_name:
        icon_name = icon_name.lower().replace(" ", "-")

    display_name = clean_app_display_name(raw_name, process_name)
    return display_name, process_name, pid, icon_name


def make_app_group_key(
    display_name: str,
    process_name: Optional[str],
    pid: Optional[int],
) -> str:
    """
    Builds a stable grouping key for an application across multiple sink inputs
    and across stream/PID recreations (e.g. during Bluetooth sink switches).
    """
    if process_name:
        bin_name = os.path.basename(process_name).strip().lower()
        is_generic = bin_name in GENERIC_BINARIES or bin_name.startswith("python3.")
        if bin_name and not is_generic:
            slug = _slugify(bin_name)
            if slug:
                return f"app:proc_{slug}"

    norm_display = (display_name or "").strip().lower()
    if norm_display and norm_display not in GENERIC_DISPLAY_NAMES:
        slug = _slugify(norm_display)
        if slug:
            return f"app:name_{slug}"

    if pid:
        return f"app:pid_{pid}"

    fallback_slug = _slugify(display_name or process_name or "unknown") or "unknown"
    return f"app:name_{fallback_slug}"


def is_bluetooth_source(source_info: Any) -> bool:
    """Returns True if a PulseAudio/PipeWire source represents a Bluetooth device."""
    proplist = getattr(source_info, "proplist", {}) or {}
    device_bus = str(proplist.get("device.bus", "")).lower()
    device_api = str(proplist.get("device.api", "")).lower()
    name = str(getattr(source_info, "name", "") or "").lower()
    return (
        device_bus == "bluetooth"
        or "bluetooth" in device_api
        or "bluez" in device_api
        or "bluez" in name
    )


def format_microphone_name(source_info: Any) -> str:
    """
    Formats a user-friendly and clear title for recording input sources / microphones.
    """
    desc = getattr(source_info, "description", "") or getattr(source_info, "name", "Мікрофон")
    port_active = getattr(source_info, "port_active", None)
    port_desc = port_active.description if port_active else ""
    port_name = port_active.name if port_active else ""

    proplist = getattr(source_info, "proplist", {}) or {}
    bus = str(proplist.get("device.bus", "")).lower()
    bt = is_bluetooth_source(source_info)

    if bt:
        if "bluetooth" in desc.lower() or "bt" in desc.lower():
            return desc
        return f"Bluetooth: {desc}"

    if port_desc and ("мікрофон" in port_desc.lower() or "mic" in port_desc.lower() or "гарнітура" in port_desc.lower()):
        return f"{port_desc} ({desc})" if desc and desc not in port_desc else port_desc

    if "analog-input-internal-mic" in port_name or "internal-mic" in port_name:
        return f"Вбудований мікрофон ({desc})"

    if "headset-mic" in port_name:
        return f"Мікрофон гарнітури ({desc})"

    if bus == "usb" or "usb" in desc.lower():
        if "мікрофон" not in desc.lower() and "mic" not in desc.lower():
            return f"USB Мікрофон: {desc}"
        return f"USB {desc}"

    if "мікрофон" not in desc.lower() and "mic" not in desc.lower():
        return f"Мікрофон: {desc}"

    return desc

import os
import psutil
from typing import Dict, Any, Optional, Tuple


def clean_app_display_name(name: str, process_name: Optional[str] = None) -> str:
    """
    Cleans up noisy Linux application names into friendly display titles.
    """
    if not name or name == "Unknown Application":
        if process_name:
            name = process_name
        else:
            return "Невідома програма"

    # Known name mappings
    name_mappings = {
        "viberpc": "Viber",
        "viber": "Viber",
        "spotify": "Spotify",
        "firefox": "Firefox",
        "google-chrome": "Google Chrome",
        "chromium": "Chromium",
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
    Extracts (display_name, process_name, pid, icon_name) from PulseAudio proplist.
    """
    pid: Optional[int] = None
    pid_str = proplist.get("application.process.id")
    if pid_str:
        try:
            pid = int(pid_str)
        except (ValueError, TypeError):
            pid = None

    process_name: Optional[str] = proplist.get("application.process.binary")
    raw_name: str = (
        proplist.get("application.name")
        or proplist.get("application.process.binary")
        or proplist.get("media.name")
        or proplist.get("window.name")
        or "Unknown Application"
    )
    icon_name: Optional[str] = (
        proplist.get("application.icon_name")
        or proplist.get("application.process.binary")
        or proplist.get("application.name")
    )

    if icon_name:
        icon_name = icon_name.lower().replace(" ", "-")

    # If PID is known and process_name is missing, resolve via psutil
    if pid and not process_name:
        try:
            p = psutil.Process(pid)
            process_name = p.name()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

    display_name = clean_app_display_name(raw_name, process_name)
    return display_name, process_name, pid, icon_name


def format_microphone_name(source_info: Any) -> str:
    """
    Formats a user-friendly and clear title for recording input sources / microphones.
    """
    desc = getattr(source_info, "description", "") or getattr(source_info, "name", "Мікрофон")
    port_active = getattr(source_info, "port_active", None)
    port_desc = port_active.description if port_active else ""
    port_name = port_active.name if port_active else ""

    proplist = getattr(source_info, "proplist", {})
    bus = proplist.get("device.bus", "")
    card_name = proplist.get("alsa.card_name", "")

    # If port has clear description like "Вбудований мікрофон", "Мікрофон гарнітури", etc.
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

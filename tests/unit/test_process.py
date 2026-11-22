from types import SimpleNamespace

from s_audio_pin.audio.process_info import (
    extract_process_info,
    format_microphone_name,
    is_bluetooth_source,
    make_app_group_key,
)


def test_extract_process_info_clean():
    proplist = {
        "application.name": "Spotify Music",
        "application.process.binary": "/usr/bin/spotify",
        "application.process.id": "12345",
        "application.icon_name": "spotify-client",
    }
    display, proc, pid, icon = extract_process_info(proplist)
    assert display == "Spotify Music"
    assert proc == "spotify"
    assert pid == 12345
    assert icon == "spotify-client"


def test_extract_process_info_fallback():
    proplist = {
        "media.name": "Playback Stream",
        "application.process.id": "invalid_pid",
    }
    display, proc, pid, icon = extract_process_info(proplist)
    assert display == "Playback Stream"
    assert pid is None


def test_is_bluetooth_source():
    bt_bus = SimpleNamespace(name="alsa_x", proplist={"device.bus": "bluetooth"})
    bt_api = SimpleNamespace(name="other", proplist={"device.api": "bluez5"})
    bt_name = SimpleNamespace(name="bluez_input.AA_BB_CC_DD_EE_FF.0", proplist={})
    wired = SimpleNamespace(name="alsa_input.pci-0000.analog-stereo", proplist={"device.bus": "pci"})

    assert is_bluetooth_source(bt_bus) is True
    assert is_bluetooth_source(bt_api) is True
    assert is_bluetooth_source(bt_name) is True
    assert is_bluetooth_source(wired) is False


def test_format_microphone_name():
    bt_src = SimpleNamespace(
        name="bluez_input.AA_BB.0",
        description="WH-1000XM5",
        port_active=None,
        proplist={"device.bus": "bluetooth"},
    )
    usb_src = SimpleNamespace(
        name="alsa_input.usb-Blue",
        description="Blue Yeti",
        port_active=None,
        proplist={"device.bus": "usb"},
    )
    internal_src = SimpleNamespace(
        name="alsa_input.pci",
        description="Built-in Audio",
        port_active=SimpleNamespace(name="analog-input-internal-mic", description="Internal Microphone"),
        proplist={},
    )
    assert format_microphone_name(bt_src) == "Bluetooth: WH-1000XM5"
    assert format_microphone_name(usb_src) == "USB Мікрофон: Blue Yeti"
    assert "Internal Microphone" in format_microphone_name(internal_src)


def test_make_app_group_key():
    # Same non-generic binary groups across PID changes (e.g. multi-tab browser / sink restart)
    k1 = make_app_group_key("Firefox", "firefox", 101)
    k2 = make_app_group_key("YouTube — Mozilla Firefox", "firefox", 202)
    assert k1 == "app:proc_firefox"
    assert k1 == k2

    # Generic interpreter disambiguates by display_name or pid
    g1 = make_app_group_key("My Audio App", "python3", 301)
    g2 = make_app_group_key("Another App", "python3", 302)
    g3 = make_app_group_key("python3", "python3", 303)
    assert g1 != g2
    assert g1 == "app:name_my_audio_app"
    assert g3 == "app:pid_303"

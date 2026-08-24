from src.audio.process_info import extract_process_info


def test_extract_process_info_clean():
    proplist = {
        "application.name": "Spotify Music",
        "application.process.binary": "spotify",
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

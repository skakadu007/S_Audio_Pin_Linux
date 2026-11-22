import atexit
import os
import shutil
import tempfile
import pytest

# Ensure pytest never touches the user's real ~/.config on initial module import
_TEST_XDG_DIR = tempfile.mkdtemp(prefix="s_audio_pin_pytest_xdg_")
os.environ.setdefault("XDG_CONFIG_HOME", _TEST_XDG_DIR)
atexit.register(shutil.rmtree, _TEST_XDG_DIR, True)


@pytest.fixture(autouse=True)
def isolate_app_state(tmp_path):
    """
    Isolates settings_manager, audio_recorder, audio_monitor, and FastAPI app.state
    for every test so ~/.config and ~/Recordings are never modified.
    """
    from s_audio_pin.audio.monitor import audio_monitor
    from s_audio_pin.audio.recorder import audio_recorder
    from s_audio_pin.config.settings import settings_manager
    from s_audio_pin.models.audio import RecordingConfig
    from s_audio_pin.server.app import app

    rec_dir = tmp_path / "recordings"
    rec_dir.mkdir(parents=True, exist_ok=True)
    cfg_path = tmp_path / "config" / "config.json"

    settings_manager._explicit_path = True
    settings_manager.config_path = cfg_path
    settings_manager.config_dir = cfg_path.parent
    settings_manager._config = RecordingConfig(output_dir=str(rec_dir))
    settings_manager.save()

    app.state.api_token = None
    app.state.shutdown_callback = None

    audio_recorder.current_session = None
    audio_recorder._workers.clear()
    audio_recorder._temp_stem_files.clear()
    audio_monitor.set_monitored_mics([])

    yield

    audio_recorder.current_session = None
    audio_recorder._workers.clear()
    audio_recorder._temp_stem_files.clear()
    audio_monitor.set_monitored_mics([])
    app.state.api_token = None
    app.state.shutdown_callback = None


@pytest.fixture
def sample_app_source():
    return {
        "id": "app:proc_spotify",
        "type": "app",
        "index": 1519,
        "name": "Spotify",
        "process_name": "spotify",
        "pid": 4892,
        "icon_name": "spotify",
        "channels": 2,
        "sample_rate": 48000,
        "volume": 1.0,
        "is_muted": False,
        "peak_level": 0.65,
        "is_selected": False,
        "is_bluetooth": False,
        "stream_indices": [1519],
        "stream_sinks": {1519: 1},
    }


@pytest.fixture
def sample_mic_source():
    return {
        "id": "source:1807",
        "type": "mic",
        "index": 1807,
        "name": "Built-in Audio Analog Stereo",
        "process_name": None,
        "pid": None,
        "icon_name": "audio-input-microphone",
        "channels": 2,
        "sample_rate": 48000,
        "volume": 0.85,
        "is_muted": False,
        "peak_level": 0.15,
        "is_selected": False,
        "is_bluetooth": False,
        "device_name": "alsa_input.pci-0000_00_1f.3.analog-stereo",
    }

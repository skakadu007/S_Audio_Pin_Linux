import pytest
from unittest.mock import MagicMock

@pytest.fixture
def sample_app_source():
    return {
        "id": "sink_input:1519",
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
    }

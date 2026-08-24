import pytest
from unittest.mock import MagicMock, patch
from src.audio.monitor import AudioMonitor
from src.models.audio import AudioSource


def test_audio_source_creation():
    src = AudioSource(
        id="sink_input:100",
        type="app",
        index=100,
        name="VLC Media Player",
        process_name="vlc",
        pid=1234,
        volume=1.0,
        is_muted=False,
        peak_level=0.5,
    )
    d = src.to_dict()
    assert d["id"] == "sink_input:100"
    assert d["name"] == "VLC Media Player"
    assert d["peak_level"] == 0.5
    assert d["type"] == "app"


def test_monitor_peak_decay():
    monitor = AudioMonitor()
    # Test smooth decay filter
    decayed = monitor._apply_decay(prev_peak=0.8, new_peak=0.2)
    assert 0.2 < decayed < 0.8
    # Test rising peak (instant rise)
    rising = monitor._apply_decay(prev_peak=0.2, new_peak=0.9)
    assert rising == 0.9

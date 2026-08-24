from pathlib import Path
from src.audio.recorder import sanitize_filename, AudioRecorder
from src.models.audio import RecordingConfig, AudioSource


def test_sanitize_filename():
    assert sanitize_filename("Spotify Music / Player") == "Spotify_Music_Player"
    assert sanitize_filename("Firefox (YouTube - Song)") == "Firefox_YouTube_Song"
    assert sanitize_filename("   ") == "audio_source"


def test_audio_recorder_idle_status():
    recorder = AudioRecorder()
    status = recorder.get_status()
    assert status["status"] == "idle"
    assert status["is_recording"] is False
    assert status["duration_secs"] == 0.0

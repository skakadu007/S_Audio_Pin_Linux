import array
import io
import subprocess
import time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from s_audio_pin.audio.recorder import (
    AudioRecorder,
    ResilientSourceCaptureWorker,
    mix_pcm_s16le_frames,
    sanitize_filename,
)
from s_audio_pin.models.audio import AudioSource, RecordingConfig


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
    assert status["reconnections"] == 0


def test_mix_pcm_s16le_frames_clamping():
    # Single frame passthrough
    f_single = array.array("h", [100, -200]).tobytes()
    assert mix_pcm_s16le_frames([f_single]) == f_single

    # Two frames exceeding int16 bounds clamp cleanly to [-32768, 32767]
    f1 = array.array("h", [25000, -25000, 1000]).tobytes()
    f2 = array.array("h", [20000, -20000, -500]).tobytes()
    mixed = array.array("h")
    mixed.frombytes(mix_pcm_s16le_frames([f1, f2]))
    assert list(mixed) == [32767, -32768, 500]


def test_resilient_worker_survives_parec_drop_and_sink_switch(tmp_path):
    frame_bytes = int(48000 * 0.02) * 4  # 3840 bytes
    sample_frame = b"\x01\x00" * (frame_bytes // 2)

    state = {"phase": 1, "parec_spawns": 0}
    captured_ffmpeg_bytes = bytearray()

    class FakeStdin:
        def __init__(self):
            self.closed = False

        def write(self, data):
            captured_ffmpeg_bytes.extend(data)
            return len(data)

        def flush(self):
            pass

        def close(self):
            self.closed = True

    class FakeFfmpegProc:
        def __init__(self):
            self.stdin = FakeStdin()
            self.stderr = io.BytesIO(b"")
            self.returncode = None

        def poll(self):
            return self.returncode

        def wait(self, timeout=None):
            self.returncode = 0
            return 0

    class FakeParecStdout:
        def __init__(self, spawn_id):
            self.spawn_id = spawn_id
            self.chunks_sent = 0
            self.closed = False

        def read(self, n):
            if self.closed:
                return b""
            if self.spawn_id == 1:
                if self.chunks_sent < 3:
                    self.chunks_sent += 1
                    time.sleep(0.01)
                    return sample_frame[:n]
                # Simulate abrupt drop on Bluetooth sink switch
                return b""
            # Reconnected stream continues producing frames until stopped
            if self.chunks_sent < 6:
                self.chunks_sent += 1
                time.sleep(0.015)
                return sample_frame[:n]
            time.sleep(0.02)
            return b""

        def close(self):
            self.closed = True

    class FakeParecProc:
        def __init__(self, spawn_id):
            self.stdout = FakeParecStdout(spawn_id)
            self.stderr = io.BytesIO(b"")
            self.returncode = None

        def poll(self):
            if self.stdout.spawn_id == 1 and self.stdout.chunks_sent >= 3 and self.returncode is None:
                self.returncode = 1
            return self.returncode

        def terminate(self):
            self.returncode = 0
            self.stdout.closed = True

        def wait(self, timeout=None):
            if self.returncode is None:
                self.returncode = 0
            return self.returncode

        def kill(self):
            self.returncode = -9

    fake_ffmpeg = FakeFfmpegProc()

    def fake_popen(cmd, **kwargs):
        if cmd[0] == "ffmpeg":
            return fake_ffmpeg
        state["parec_spawns"] += 1
        return FakeParecProc(state["parec_spawns"])

    class FakeMonitor:
        def get_live_streams_for_source(self, source):
            if state["phase"] == 1:
                return {"streams": [(101, 1)], "found": True}
            return {"streams": [(202, 2)], "found": True}

    src = AudioSource(
        id="app:proc_spotify",
        type="app",
        index=101,
        name="Spotify",
        process_name="spotify",
        stream_indices=[101],
        stream_sinks={101: 1},
    )
    cfg = RecordingConfig(format="wav", sample_rate=48000, output_dir=str(tmp_path))

    with patch("s_audio_pin.audio.recorder.subprocess.Popen", side_effect=fake_popen):
        worker = ResilientSourceCaptureWorker(
            source=src,
            output_path=tmp_path / "out.wav",
            config=cfg,
            monitor=FakeMonitor(),
        )
        worker.start()
        time.sleep(0.32)
        state["phase"] = 2
        time.sleep(0.42)
        worker.stop()

    assert state["parec_spawns"] >= 2
    assert worker.reconnections >= 1
    assert len(worker.warnings) >= 1
    assert fake_ffmpeg.stdin.closed is True
    assert worker.ffmpeg_error is None
    assert len(captured_ffmpeg_bytes) >= frame_bytes * 5


def test_single_mix_mixdown_failure_preserves_temp_stems(tmp_path):
    class FakeMonitor:
        def get_sources(self):
            return {
                "apps": [
                    {
                        "id": "app:proc_firefox",
                        "type": "app",
                        "index": 11,
                        "name": "Firefox",
                        "process_name": "firefox",
                        "stream_indices": [11],
                        "stream_sinks": {11: 1},
                    }
                ],
                "mics": [
                    {
                        "id": "source:22",
                        "type": "mic",
                        "index": 22,
                        "name": "Mic",
                        "device_name": "alsa_input.pci",
                        "stream_indices": [22],
                    }
                ],
            }

        def set_recording_active(self, active):
            pass

    class DummyWorker:
        def __init__(self, source, output_path, config, monitor, session_start_monotonic=None):
            self.source = source
            self.output_path = output_path
            self.reconnections = 0
            self.warnings = []
            self.ffmpeg_error = None
            import threading
            self._state_lock = threading.Lock()

        def start(self):
            # Write >44 bytes dummy WAV header + payload so stem counts as non-empty
            self.output_path.write_bytes(b"RIFF" + b"\x00" * 100)

        def stop(self):
            pass

    recorder = AudioRecorder(monitor=FakeMonitor())
    cfg = RecordingConfig(format="mp3", mode="single_mix", output_dir=str(tmp_path))

    with patch("s_audio_pin.audio.recorder.check_audio_dependencies", return_value={"ready": True, "parec": True, "ffmpeg": True}), \
         patch("s_audio_pin.audio.recorder.ResilientSourceCaptureWorker", side_effect=DummyWorker), \
         patch("s_audio_pin.audio.recorder.subprocess.run", return_value=SimpleNamespace(returncode=1, stderr="mock mix failure")):
        ok, session, err = recorder.start_recording(["app:proc_firefox", "source:22"], config=cfg)
        assert ok is True
        stop_ok, stop_session, stop_err = recorder.stop_recording()

    assert stop_ok is False
    assert stop_session.status == "error"
    assert "сирі доріжки збережено" in stop_err
    temp_dirs = list(tmp_path.glob(".tmp_*"))
    assert len(temp_dirs) == 1
    assert (temp_dirs[0] / "stem_1.wav").exists()
    assert (temp_dirs[0] / "stem_2.wav").exists()

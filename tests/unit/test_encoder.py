from pathlib import Path
from src.audio.encoder import build_ffmpeg_single_encoder_cmd, build_ffmpeg_mix_cmd
from src.models.audio import RecordingConfig


def test_build_ffmpeg_single_encoder_mp3():
    config = RecordingConfig(format="mp3", bitrate="320k", sample_rate=48000)
    out_path = Path("/tmp/test_out.mp3")
    cmd = build_ffmpeg_single_encoder_cmd(config, out_path)
    assert "ffmpeg" in cmd[0]
    assert "-ar" in cmd
    assert "48000" in cmd
    assert "-b:a" in cmd
    assert "320k" in cmd
    assert str(out_path) == cmd[-1]


def test_build_ffmpeg_single_encoder_wav():
    config = RecordingConfig(format="wav", sample_rate=44100)
    out_path = Path("/tmp/test_out.wav")
    cmd = build_ffmpeg_single_encoder_cmd(config, out_path)
    assert "ffmpeg" in cmd[0]
    assert "-c:a" in cmd
    assert "pcm_s16le" in cmd
    assert str(out_path) == cmd[-1]

from pathlib import Path
from s_audio_pin.audio.encoder import build_ffmpeg_mix_cmd, build_ffmpeg_single_encoder_cmd
from s_audio_pin.models.audio import RecordingConfig


def test_build_ffmpeg_single_encoder_mp3():
    config = RecordingConfig(format="mp3", bitrate="320k", sample_rate=48000)
    out_path = Path("/tmp/test_out.mp3")
    cmd = build_ffmpeg_single_encoder_cmd(config, out_path)
    assert cmd[0] == "ffmpeg"
    assert "-ar" in cmd and "48000" in cmd
    assert "-c:a" in cmd and "libmp3lame" in cmd
    assert "-b:a" in cmd and "320k" in cmd
    assert str(out_path) == cmd[-1]


def test_build_ffmpeg_single_encoder_wav():
    config = RecordingConfig(format="wav", sample_rate=44100)
    out_path = Path("/tmp/test_out.wav")
    cmd = build_ffmpeg_single_encoder_cmd(config, out_path)
    assert "-ar" in cmd and "44100" in cmd
    assert "pcm_s16le" in cmd
    assert str(out_path) == cmd[-1]


def test_build_ffmpeg_single_encoder_flac():
    config = RecordingConfig(format="flac", sample_rate=48000)
    out_path = Path("/tmp/test_out.flac")
    cmd = build_ffmpeg_single_encoder_cmd(config, out_path)
    assert "flac" in cmd
    assert "-compression_level" in cmd
    assert str(out_path) == cmd[-1]


def test_build_ffmpeg_single_encoder_ogg():
    config = RecordingConfig(format="ogg", bitrate="192k", sample_rate=48000)
    out_path = Path("/tmp/test_out.ogg")
    cmd = build_ffmpeg_single_encoder_cmd(config, out_path)
    assert "libopus" in cmd
    assert "192k" in cmd
    assert str(out_path) == cmd[-1]


def test_build_ffmpeg_mix_cmd_with_limiter():
    config = RecordingConfig(format="mp3", bitrate="256k")
    inputs = [Path("/tmp/stem1.wav"), Path("/tmp/stem2.wav")]
    out_path = Path("/tmp/mix.mp3")
    cmd = build_ffmpeg_mix_cmd(inputs, config, out_path)
    assert "-filter_complex" in cmd
    fc = cmd[cmd.index("-filter_complex") + 1]
    assert "amix=inputs=2" in fc
    assert "alimiter=limit=0.95" in fc
    assert "libmp3lame" in cmd
    assert str(out_path) == cmd[-1]

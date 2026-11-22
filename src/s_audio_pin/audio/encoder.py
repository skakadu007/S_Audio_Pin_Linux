from pathlib import Path
from typing import List
from ..models.audio import RecordingConfig


def _codec_args(config: RecordingConfig) -> List[str]:
    """Returns FFmpeg audio codec and quality arguments for the configured format."""
    fmt = config.format
    if fmt == "mp3":
        return ["-c:a", "libmp3lame", "-b:a", config.bitrate]
    if fmt == "flac":
        return ["-c:a", "flac", "-compression_level", "5"]
    if fmt == "ogg":
        return ["-c:a", "libopus", "-b:a", config.bitrate]
    # wav (default lossless PCM)
    return ["-c:a", "pcm_s16le"]


def build_ffmpeg_single_encoder_cmd(config: RecordingConfig, output_path: Path) -> List[str]:
    """
    Builds an FFmpeg command to read raw s16le stereo PCM from stdin and encode to output_path.
    """
    cmd = [
        "ffmpeg",
        "-y",
        "-f", "s16le",
        "-ar", str(config.sample_rate),
        "-ac", "2",
        "-i", "pipe:0",
    ]
    cmd.extend(_codec_args(config))
    cmd.append(str(output_path))
    return cmd


def build_ffmpeg_mix_cmd(input_files: List[Path], config: RecordingConfig, output_path: Path) -> List[str]:
    """
    Mixes multiple audio tracks together into a single combined output file using ffmpeg amix + alimiter.
    """
    if len(input_files) == 1:
        cmd = ["ffmpeg", "-y", "-i", str(input_files[0])]
        cmd.extend(_codec_args(config))
        cmd.append(str(output_path))
        return cmd

    cmd = ["ffmpeg", "-y"]
    for f in input_files:
        cmd.extend(["-i", str(f)])

    filter_str = (
        f"amix=inputs={len(input_files)}:duration=longest:dropout_transition=0:normalize=0,"
        "alimiter=limit=0.95:attack=5:release=50"
    )
    cmd.extend(["-filter_complex", filter_str])
    cmd.extend(_codec_args(config))
    cmd.append(str(output_path))
    return cmd

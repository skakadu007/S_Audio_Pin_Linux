from pathlib import Path
from typing import List
from ..models.audio import RecordingConfig


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

    if config.format == "mp3":
        cmd.extend([
            "-c:a", "libmp3lame",
            "-b:a", config.bitrate,
        ])
    else:  # wav
        cmd.extend([
            "-c:a", "pcm_s16le",
        ])

    cmd.append(str(output_path))
    return cmd


def build_ffmpeg_mix_cmd(input_files: List[Path], config: RecordingConfig, output_path: Path) -> List[str]:
    """
    Mixes multiple audio tracks together into a single combined output file using ffmpeg amix filter.
    """
    if len(input_files) == 1:
        # Just convert/copy single file to final destination
        cmd = ["ffmpeg", "-y", "-i", str(input_files[0])]
        if config.format == "mp3":
            cmd.extend(["-c:a", "libmp3lame", "-b:a", config.bitrate])
        else:
            cmd.extend(["-c:a", "pcm_s16le"])
        cmd.append(str(output_path))
        return cmd

    cmd = ["ffmpeg", "-y"]
    for f in input_files:
        cmd.extend(["-i", str(f)])

    filter_str = f"amix=inputs={len(input_files)}:duration=longest:dropout_transition=2:normalize=0"
    cmd.extend(["-filter_complex", filter_str])

    if config.format == "mp3":
        cmd.extend(["-c:a", "libmp3lame", "-b:a", config.bitrate])
    else:
        cmd.extend(["-c:a", "pcm_s16le"])

    cmd.append(str(output_path))
    return cmd

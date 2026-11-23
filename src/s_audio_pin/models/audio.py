import os
from dataclasses import dataclass, field, asdict, replace
from pathlib import Path
from typing import Optional, List, Literal, Dict, Any

SourceType = Literal["app", "mic"]
AudioFormat = Literal["mp3", "wav", "flac", "ogg"]
AudioBitrate = Literal["128k", "192k", "256k", "320k"]
RecordingMode = Literal["single_mix", "multi_stem"]
SessionStatus = Literal["idle", "recording", "finalizing", "completed", "error"]


def _resolve_xdg_music_dir() -> Path:
    """
    Resolves the localized XDG Music directory (e.g. ~/Music or ~/Музика),
    using env XDG_MUSIC_DIR, GLib user-special-dir, or user-dirs.dirs.
    """
    env_music = os.environ.get("XDG_MUSIC_DIR", "").strip()
    if env_music:
        return Path(env_music).expanduser()

    try:
        from gi.repository import GLib  # type: ignore[import-not-found]

        glib_dir = GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_MUSIC)
        if glib_dir:
            return Path(glib_dir).expanduser()
    except Exception:
        pass

    xdg_cfg = os.environ.get("XDG_CONFIG_HOME", "").strip()
    cfg_base = Path(xdg_cfg).expanduser() if xdg_cfg else (Path.home() / ".config")
    user_dirs = cfg_base / "user-dirs.dirs"
    if user_dirs.exists():
        try:
            for raw_line in user_dirs.read_text(encoding="utf-8", errors="replace").splitlines():
                line = raw_line.strip()
                if not line or line.startswith("#") or not line.startswith("XDG_MUSIC_DIR="):
                    continue
                val = line.split("=", 1)[1].strip().strip('"').strip("'")
                val = val.replace("${HOME}", str(Path.home())).replace("$HOME", str(Path.home()))
                if val:
                    return Path(val).expanduser()
        except OSError:
            pass

    return Path.home() / "Music"


def get_default_recordings_dir() -> str:
    """
    Returns a portable default directory for saved recordings.
    Inside Flatpak, defaults to the localized XDG Music directory to match sandbox access.
    On host Linux, defaults to ~/Recordings/S_Audio_Pin.
    """
    if Path("/.flatpak-info").exists():
        return str(_resolve_xdg_music_dir() / "S_Audio_Pin")
    return str(Path.home() / "Recordings" / "S_Audio_Pin")


@dataclass
class AudioSource:
    id: str
    type: SourceType
    index: int
    name: str
    process_name: Optional[str] = None
    pid: Optional[int] = None
    icon_name: Optional[str] = None
    channels: int = 2
    sample_rate: int = 48000
    volume: float = 1.0
    is_muted: bool = False
    peak_level: float = 0.0
    is_selected: bool = False
    stream_indices: List[int] = field(default_factory=list)
    device_name: Optional[str] = None
    stream_count: int = 1
    is_bluetooth: bool = False
    stream_sinks: Dict[int, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        if not self.stream_indices:
            d["stream_indices"] = [self.index]
        return d


@dataclass
class RecordingConfig:
    format: AudioFormat = "mp3"
    bitrate: AudioBitrate = "320k"
    sample_rate: int = 48000
    mode: RecordingMode = "single_mix"
    output_dir: str = field(default_factory=get_default_recordings_dir)
    filename_prefix: str = "rec"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def clone(self, **overrides: Any) -> "RecordingConfig":
        """Returns a copy of this config with non-None overrides applied."""
        valid_keys = {
            "format", "bitrate", "sample_rate", "mode", "output_dir", "filename_prefix"
        }
        filtered = {
            k: v for k, v in overrides.items() if k in valid_keys and v is not None
        }
        return replace(self, **filtered)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RecordingConfig":
        valid_keys = {
            "format", "bitrate", "sample_rate", "mode", "output_dir", "filename_prefix"
        }
        filtered = {k: v for k, v in data.items() if k in valid_keys and v is not None}
        return cls(**filtered)


@dataclass
class RecordingSession:
    session_id: str
    status: SessionStatus = "idle"
    start_time: Optional[float] = None
    duration_secs: float = 0.0
    config: RecordingConfig = field(default_factory=RecordingConfig)
    sources: List[AudioSource] = field(default_factory=list)
    output_files: List[str] = field(default_factory=list)
    total_bytes: int = 0
    error_message: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    reconnections: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "status": self.status,
            "start_time": self.start_time,
            "duration_secs": self.duration_secs,
            "config": self.config.to_dict(),
            "sources": [s.to_dict() for s in self.sources],
            "output_files": self.output_files,
            "total_bytes": self.total_bytes,
            "error_message": self.error_message,
            "warnings": list(self.warnings),
            "reconnections": self.reconnections,
        }

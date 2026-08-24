from dataclasses import dataclass, field, asdict
from typing import Optional, List, Literal, Dict, Any

SourceType = Literal["app", "mic"]
AudioFormat = Literal["wav", "mp3"]
AudioBitrate = Literal["128k", "192k", "256k", "320k"]
RecordingMode = Literal["single_mix", "multi_stem"]
SessionStatus = Literal["idle", "recording", "finalizing", "completed", "error"]


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
    output_dir: str = "/home/s_linux/Recordings/S_Audio_Pin"
    filename_prefix: str = "rec"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

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
        }

import os
import signal
import time
import subprocess
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from ..models.audio import AudioSource, RecordingConfig, RecordingSession, SessionStatus
from ..config.settings import settings_manager
from .encoder import build_ffmpeg_single_encoder_cmd, build_ffmpeg_mix_cmd
from .monitor import audio_monitor

logger = logging.getLogger("s_audio_pin.recorder")


def sanitize_filename(name: str) -> str:
    s = re.sub(r'[^\w\s-]', '', name).strip()
    return re.sub(r'[-\s]+', '_', s) or "audio_source"


class SingleStreamCaptureWorker:
    """Manages parec -> ffmpeg recording pipeline for a single stream index or mic device."""
    def __init__(self, is_app: bool, stream_index: int, output_path: Path, config: RecordingConfig):
        self.is_app = is_app
        self.stream_index = stream_index
        self.output_path = output_path
        self.config = config
        self.parec_proc: Optional[subprocess.Popen] = None
        self.ffmpeg_proc: Optional[subprocess.Popen] = None

    def start(self):
        if self.is_app:
            parec_cmd = [
                "parec",
                "--format=s16le",
                f"--rate={self.config.sample_rate}",
                "--channels=2",
                f"--monitor-stream={self.stream_index}",
            ]
        else:
            parec_cmd = [
                "parec",
                "--format=s16le",
                f"--rate={self.config.sample_rate}",
                "--channels=2",
                "-d", str(self.stream_index),
            ]

        ffmpeg_cmd = build_ffmpeg_single_encoder_cmd(self.config, self.output_path)

        logger.info(f"Starting stream capture worker index={self.stream_index} -> {self.output_path}")
        self.parec_proc = subprocess.Popen(
            parec_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            bufsize=1024 * 16,
        )

        self.ffmpeg_proc = subprocess.Popen(
            ffmpeg_cmd,
            stdin=self.parec_proc.stdout,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        if self.parec_proc.stdout:
            self.parec_proc.stdout.close()

    def stop(self):
        if self.parec_proc and self.parec_proc.poll() is None:
            try:
                self.parec_proc.send_signal(signal.SIGINT)
                self.parec_proc.wait(timeout=1.0)
            except Exception:
                self.parec_proc.kill()

        if self.ffmpeg_proc and self.ffmpeg_proc.poll() is None:
            try:
                self.ffmpeg_proc.send_signal(signal.SIGINT)
                self.ffmpeg_proc.wait(timeout=2.0)
            except Exception:
                self.ffmpeg_proc.kill()


class AudioRecorder:
    def __init__(self):
        self.current_session: Optional[RecordingSession] = None
        self._workers: List[SingleStreamCaptureWorker] = []
        self._temp_stem_files: List[Path] = []

    @property
    def is_recording(self) -> bool:
        return self.current_session is not None and self.current_session.status == "recording"

    def get_status(self) -> Dict[str, Any]:
        if not self.current_session:
            return {
                "status": "idle",
                "is_recording": False,
                "duration_secs": 0.0,
                "session": None,
            }

        duration = 0.0
        if self.current_session.start_time:
            if self.current_session.status == "recording":
                duration = time.time() - self.current_session.start_time
            else:
                duration = self.current_session.duration_secs

        return {
            "status": self.current_session.status,
            "is_recording": self.current_session.status == "recording",
            "duration_secs": round(duration, 1),
            "session": self.current_session.to_dict(),
        }

    def start_recording(
        self,
        source_ids: List[str],
        config: Optional[RecordingConfig] = None,
    ) -> Tuple[bool, Optional[RecordingSession], str]:
        if self.is_recording:
            return False, None, "Recording is already in progress"

        if not source_ids:
            return False, None, "No audio sources selected for recording"

        cfg = config or settings_manager.config
        output_dir = Path(cfg.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Match selected source IDs from live monitor
        sources_dict = audio_monitor.get_sources()
        all_sources = sources_dict.get("apps", []) + sources_dict.get("mics", [])
        sources_by_id = {s["id"]: s for s in all_sources}

        selected_sources: List[AudioSource] = []
        for sid in source_ids:
            if sid in sources_by_id:
                s_data = sources_by_id[sid]
                selected_sources.append(
                    AudioSource(
                        id=s_data["id"],
                        type=s_data["type"],
                        index=s_data["index"],
                        name=s_data["name"],
                        process_name=s_data.get("process_name"),
                        pid=s_data.get("pid"),
                        icon_name=s_data.get("icon_name"),
                        channels=s_data.get("channels", 2),
                        sample_rate=s_data.get("sample_rate", 48000),
                        volume=s_data.get("volume", 1.0),
                        is_muted=s_data.get("is_muted", False),
                        is_selected=True,
                        stream_indices=s_data.get("stream_indices", [s_data["index"]]),
                        stream_count=s_data.get("stream_count", 1),
                    )
                )

        if not selected_sources:
            return False, None, "None of the selected audio sources are currently active"

        timestamp_str = time.strftime("%Y%m%d_%H%M%S")
        session_id = f"rec_{timestamp_str}"

        self.current_session = RecordingSession(
            session_id=session_id,
            status="recording",
            start_time=time.time(),
            config=cfg,
            sources=selected_sources,
            output_files=[],
        )

        self._workers.clear()
        self._temp_stem_files.clear()

        # Collect all individual stream tasks
        all_stream_tasks = []
        for src in selected_sources:
            indices = src.stream_indices if src.stream_indices else [src.index]
            for s_idx in indices:
                all_stream_tasks.append({
                    "is_app": src.type == "app",
                    "stream_index": s_idx,
                    "source_name": src.name,
                    "source_id": src.id,
                })

        if cfg.mode == "multi_stem":
            # Session directory for multi-track stems
            session_folder = output_dir / session_id
            session_folder.mkdir(parents=True, exist_ok=True)

            for idx, task in enumerate(all_stream_tasks, 1):
                clean_name = sanitize_filename(task["source_name"])
                stem_file = session_folder / f"{idx:02d}_{clean_name}_stream{task['stream_index']}.{cfg.format}"
                worker = SingleStreamCaptureWorker(task["is_app"], task["stream_index"], stem_file, cfg)
                self._workers.append(worker)
                self.current_session.output_files.append(str(stem_file))
                worker.start()

        else:
            # Single Master Mix mode
            if len(all_stream_tasks) == 1:
                task = all_stream_tasks[0]
                clean_name = sanitize_filename(task["source_name"])
                final_file = output_dir / f"{session_id}_{clean_name}.{cfg.format}"
                worker = SingleStreamCaptureWorker(task["is_app"], task["stream_index"], final_file, cfg)
                self._workers.append(worker)
                self.current_session.output_files.append(str(final_file))
                worker.start()
            else:
                temp_folder = output_dir / f".tmp_{session_id}"
                temp_folder.mkdir(parents=True, exist_ok=True)
                for idx, task in enumerate(all_stream_tasks, 1):
                    temp_stem = temp_folder / f"stem_{idx}.wav"
                    temp_cfg = RecordingConfig(
                        format="wav",
                        sample_rate=cfg.sample_rate,
                        mode="single_mix",
                    )
                    worker = SingleStreamCaptureWorker(task["is_app"], task["stream_index"], temp_stem, temp_cfg)
                    self._workers.append(worker)
                    self._temp_stem_files.append(temp_stem)
                    worker.start()

                final_mix_file = output_dir / f"{session_id}_mix.{cfg.format}"
                self.current_session.output_files.append(str(final_mix_file))

        logger.info(f"Recording session {session_id} started with {len(all_stream_tasks)} capture workers.")
        return True, self.current_session, ""

    def stop_recording(self) -> Tuple[bool, Optional[RecordingSession], str]:
        if not self.is_recording or not self.current_session:
            return False, None, "No active recording session to stop"

        session = self.current_session
        session.status = "finalizing"
        session.duration_secs = time.time() - (session.start_time or time.time())

        # Stop all capture workers
        for worker in self._workers:
            worker.stop()
        self._workers.clear()

        # If master mix from multiple temp stems, perform FFmpeg mixdown
        if session.config.mode == "single_mix" and len(self._temp_stem_files) > 1:
            try:
                final_output = Path(session.output_files[0])
                mix_cmd = build_ffmpeg_mix_cmd(self._temp_stem_files, session.config, final_output)
                logger.info(f"Mixing {len(self._temp_stem_files)} tracks into {final_output}")
                res = subprocess.run(mix_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                # Clean up temp stem folder
                if self._temp_stem_files:
                    temp_folder = self._temp_stem_files[0].parent
                    for f in self._temp_stem_files:
                        try:
                            f.unlink(missing_ok=True)
                        except Exception:
                            pass
                    try:
                        temp_folder.rmdir()
                    except Exception:
                        pass
                    self._temp_stem_files.clear()

            except Exception as e:
                logger.error(f"Error during audio mixdown: {e}")
                session.status = "error"
                session.error_message = str(e)
                return False, session, f"Mixdown error: {e}"

        # Calculate total written bytes
        total_bytes = 0
        for fpath in session.output_files:
            p = Path(fpath)
            if p.exists():
                total_bytes += p.stat().st_size

        session.total_bytes = total_bytes
        session.status = "completed"
        logger.info(f"Recording session {session.session_id} completed: {total_bytes} bytes written.")
        return True, session, ""


# Global singleton recorder instance
audio_recorder = AudioRecorder()

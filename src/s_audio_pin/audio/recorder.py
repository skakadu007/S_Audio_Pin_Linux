import array
import logging
import re
import shutil
import subprocess
import threading
import time
from collections import deque
from pathlib import Path
from typing import Any, Deque, Dict, List, Optional, Tuple

from ..config.settings import settings_manager
from ..models.audio import AudioSource, RecordingConfig, RecordingSession
from .encoder import build_ffmpeg_mix_cmd, build_ffmpeg_single_encoder_cmd
from .monitor import audio_monitor

logger = logging.getLogger("s_audio_pin.recorder")


def sanitize_filename(name: str) -> str:
    s = re.sub(r"[^\w\s-]", "", name).strip()
    return re.sub(r"[-\s]+", "_", s) or "audio_source"


def check_audio_dependencies() -> Dict[str, Any]:
    """Checks availability of required external CLI tools (parec and ffmpeg)."""
    parec_path = shutil.which("parec")
    ffmpeg_path = shutil.which("ffmpeg")
    return {
        "parec": bool(parec_path),
        "ffmpeg": bool(ffmpeg_path),
        "parec_path": parec_path,
        "ffmpeg_path": ffmpeg_path,
        "ready": bool(parec_path and ffmpeg_path),
    }


def mix_pcm_s16le_frames(frames: List[bytes]) -> bytes:
    """
    Mixes one or more equal-length s16le PCM frames with saturation clamping [-32768, 32767].
    Compatible with Python 3.11–3.14 without removed stdlib audioop.
    """
    if not frames:
        return b""
    if len(frames) == 1:
        return frames[0]

    n_samples = len(frames[0]) // 2
    if n_samples == 0:
        return b""

    first = array.array("h")
    first.frombytes(frames[0][: n_samples * 2])
    acc = list(first)

    for frame in frames[1:]:
        arr = array.array("h")
        arr.frombytes(frame[: n_samples * 2])
        for i, sample in enumerate(arr):
            acc[i] += sample

    out = array.array(
        "h",
        (32767 if v > 32767 else (-32768 if v < -32768 else v) for v in acc),
    )
    return out.tobytes()


class SubStreamReader:
    """
    Wraps a single `parec` subprocess reading fixed-size 20ms stereo s16le PCM frames
    into a bounded thread-safe queue, capturing stderr diagnostics.
    """

    def __init__(
        self,
        is_app: bool,
        target: str,
        sample_rate: int,
        frame_bytes: int,
        sink_id: Optional[int] = None,
    ):
        self.is_app = is_app
        self.target = str(target)
        self.sample_rate = sample_rate
        self.frame_bytes = frame_bytes
        self.sink_id = sink_id

        self._stop_event = threading.Event()
        self._q_lock = threading.Lock()
        self._queue: Deque[bytes] = deque(maxlen=25)
        self.stderr_lines: Deque[str] = deque(maxlen=20)
        self.last_data_monotonic: float = 0.0
        self.total_bytes_read: int = 0
        self.exit_code: Optional[int] = None

        cmd = [
            "parec",
            "--client-name=s-audio-pin-rec",
            "--stream-name=capture",
            "--format=s16le",
            f"--rate={self.sample_rate}",
            "--channels=2",
            "--latency-msec=40",
        ]
        if self.is_app:
            cmd.append(f"--monitor-stream={self.target}")
        else:
            cmd.extend(["-d", self.target])

        self.proc: Optional[subprocess.Popen] = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=max(16384, self.frame_bytes * 4),
        )
        self._stdout_thread = threading.Thread(target=self._read_stdout, daemon=True)
        self._stderr_thread = threading.Thread(target=self._read_stderr, daemon=True)
        self._stdout_thread.start()
        self._stderr_thread.start()

    @property
    def is_alive(self) -> bool:
        if self._stop_event.is_set() or self.proc is None:
            return False
        if self.proc.poll() is not None:
            return False
        return self._stdout_thread.is_alive()

    def _read_stderr(self):
        proc = self.proc
        if proc is None or proc.stderr is None:
            return
        try:
            for raw_line in proc.stderr:
                line = raw_line.decode("utf-8", errors="replace").strip()
                if line:
                    self.stderr_lines.append(line)
                    logger.debug("parec[%s] stderr: %s", self.target, line)
        except Exception:
            pass

    def _read_stdout(self):
        proc = self.proc
        if proc is None or proc.stdout is None:
            return
        buf = bytearray()
        try:
            while not self._stop_event.is_set():
                need = self.frame_bytes - len(buf)
                chunk = proc.stdout.read(need)
                if not chunk:
                    break
                buf.extend(chunk)
                while len(buf) >= self.frame_bytes:
                    frame = bytes(buf[: self.frame_bytes])
                    del buf[: self.frame_bytes]
                    with self._q_lock:
                        self._queue.append(frame)
                    self.last_data_monotonic = time.monotonic()
                    self.total_bytes_read += self.frame_bytes
        except Exception as e:
            logger.debug("SubStreamReader[%s] stdout read ended: %s", self.target, e)
        finally:
            if proc.poll() is not None:
                self.exit_code = proc.returncode

    def pop_frame(self) -> Optional[bytes]:
        with self._q_lock:
            if self._queue:
                return self._queue.popleft()
            return None

    def queue_len(self) -> int:
        with self._q_lock:
            return len(self._queue)

    def stop(self):
        self._stop_event.set()
        proc = self.proc
        if proc is not None:
            if proc.poll() is None:
                try:
                    proc.terminate()
                    proc.wait(timeout=1.0)
                except subprocess.TimeoutExpired:
                    try:
                        proc.kill()
                        proc.wait(timeout=1.0)
                    except Exception:
                        pass
                except Exception:
                    pass
            else:
                try:
                    proc.wait(timeout=0.1)
                except Exception:
                    pass
            self.exit_code = proc.returncode

            if proc.stdout is not None:
                try:
                    proc.stdout.close()
                except Exception:
                    pass
            if proc.stderr is not None:
                try:
                    proc.stderr.close()
                except Exception:
                    pass

        if self._stdout_thread.is_alive():
            self._stdout_thread.join(timeout=0.5)
        if self._stderr_thread.is_alive():
            self._stderr_thread.join(timeout=0.5)


class ResilientSourceCaptureWorker:
    """
    Captures ONE armed AudioSource into ONE persistent FFmpeg encoder.
    Automatically detects stream restarts, sink switches (e.g. speakers <-> Bluetooth),
    and dropped parec streams, feeding continuous synced PCM (with silence padding during
    handoffs) into FFmpeg so recordings never break mid-session.
    """

    def __init__(
        self,
        source: AudioSource,
        output_path: Path,
        config: RecordingConfig,
        monitor: Any,
        session_start_monotonic: Optional[float] = None,
    ):
        self.source = source
        self.output_path = output_path
        self.config = config
        self.monitor = monitor
        self.start_monotonic = session_start_monotonic or time.monotonic()

        self.tick_secs = 0.02  # 20ms frame pacing
        self.frame_samples_per_ch = int(self.config.sample_rate * self.tick_secs)
        self.frame_bytes = self.frame_samples_per_ch * 4  # stereo s16le
        self.zero_frame = b"\x00" * self.frame_bytes

        self._stop_event = threading.Event()
        self._readers: Dict[str, SubStreamReader] = {}
        self._last_restart: Dict[str, float] = {}
        self._had_disconnect = False

        self.ffmpeg_proc: Optional[subprocess.Popen] = None
        self._ffmpeg_stderr: Deque[str] = deque(maxlen=30)
        self._ffmpeg_stderr_thread: Optional[threading.Thread] = None
        self._feeder_thread: Optional[threading.Thread] = None

        self.written_bytes: int = 0
        self.reconnections: int = 0
        self.warnings: List[str] = []
        self.ffmpeg_error: Optional[str] = None
        self._state_lock = threading.Lock()

    def _add_warning(self, msg: str):
        with self._state_lock:
            if not self.warnings or self.warnings[-1] != msg:
                self.warnings.append(msg)

    def _read_ffmpeg_stderr(self):
        proc = self.ffmpeg_proc
        if proc is None or proc.stderr is None:
            return
        try:
            for raw_line in proc.stderr:
                line = raw_line.decode("utf-8", errors="replace").strip()
                if line:
                    self._ffmpeg_stderr.append(line)
        except Exception:
            pass

    def start(self):
        ffmpeg_cmd = build_ffmpeg_single_encoder_cmd(self.config, self.output_path)
        logger.info("Starting resilient capture for '%s' -> %s", self.source.name, self.output_path)

        self.ffmpeg_proc = subprocess.Popen(
            ffmpeg_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            bufsize=self.frame_bytes * 8,
        )
        self._ffmpeg_stderr_thread = threading.Thread(target=self._read_ffmpeg_stderr, daemon=True)
        self._ffmpeg_stderr_thread.start()

        self._sync_readers(initial=True)
        self._feeder_thread = threading.Thread(target=self._run_loop, daemon=True)
        self._feeder_thread.start()

    def _start_reader(self, key: str, is_app: bool, target: str, sink_id: Optional[int] = None):
        try:
            reader = SubStreamReader(
                is_app=is_app,
                target=target,
                sample_rate=self.config.sample_rate,
                frame_bytes=self.frame_bytes,
                sink_id=sink_id,
            )
            self._readers[key] = reader
        except Exception as e:
            logger.error("Failed to spawn parec reader for %s (%s): %s", self.source.name, target, e)
            self._add_warning(f"Не вдалося запустити захоплення '{self.source.name}': {e}")

    def _sync_readers(self, initial: bool = False):
        live = self.monitor.get_live_streams_for_source(self.source)
        now = time.monotonic()

        if self.source.type == "app":
            live_streams: List[Tuple[int, Optional[int]]] = (
                live.get("streams", []) if live.get("found") else []
            )
            live_map: Dict[str, Optional[int]] = {
                str(s_idx): sink_id for s_idx, sink_id in live_streams
            }

            if initial:
                for key, sink_id in live_map.items():
                    self._start_reader(key, is_app=True, target=key, sink_id=sink_id)
                return

            for key in list(self._readers.keys()):
                reader = self._readers[key]
                if key not in live_map:
                    reader.stop()
                    del self._readers[key]
                    self._had_disconnect = True
                    continue

                new_sink = live_map[key]
                if reader.sink_id != new_sink:
                    logger.info(
                        "Sink changed for '%s' stream %s (%s -> %s); reconnecting parec.",
                        self.source.name, key, reader.sink_id, new_sink,
                    )
                    reader.stop()
                    del self._readers[key]
                    self._start_reader(key, is_app=True, target=key, sink_id=new_sink)
                    with self._state_lock:
                        self.reconnections += 1
                    self._add_warning(
                        f"Перепідключено потік '{self.source.name}' після зміни пристрою виводу."
                    )
                elif not reader.is_alive:
                    if now - self._last_restart.get(key, 0.0) >= 0.3:
                        logger.warning(
                            "parec exited unexpectedly for '%s' stream %s (code=%s); restarting.",
                            self.source.name, key, reader.exit_code,
                        )
                        reader.stop()
                        del self._readers[key]
                        self._last_restart[key] = now
                        self._start_reader(key, is_app=True, target=key, sink_id=new_sink)
                        with self._state_lock:
                            self.reconnections += 1
                        self._add_warning(
                            f"Перезапущено потік '{self.source.name}' після тимчасового розриву."
                        )

            for key, sink_id in live_map.items():
                if key not in self._readers:
                    self._start_reader(key, is_app=True, target=key, sink_id=sink_id)
                    if self._had_disconnect:
                        self._had_disconnect = False
                        with self._state_lock:
                            self.reconnections += 1
                        self._add_warning(
                            f"Відновлено запис '{self.source.name}' на новому аудіопотоці."
                        )
            return

        # Microphone synchronization
        device_name: Optional[str] = live.get("device_name") if live.get("found") else None
        if initial:
            if device_name:
                self._start_reader("mic", is_app=False, target=device_name)
            return

        if not device_name:
            if "mic" in self._readers:
                self._readers["mic"].stop()
                del self._readers["mic"]
                self._had_disconnect = True
            return

        if "mic" in self._readers:
            reader = self._readers["mic"]
            if reader.target != device_name:
                logger.info(
                    "Microphone device changed for '%s' (%s -> %s); reconnecting.",
                    self.source.name, reader.target, device_name,
                )
                reader.stop()
                del self._readers["mic"]
                self._start_reader("mic", is_app=False, target=device_name)
                with self._state_lock:
                    self.reconnections += 1
                self._add_warning(
                    f"Перепідключено мікрофон '{self.source.name}' після зміни профілю."
                )
            elif not reader.is_alive:
                if now - self._last_restart.get("mic", 0.0) >= 0.3:
                    logger.warning(
                        "parec exited unexpectedly for mic '%s'; restarting.",
                        self.source.name,
                    )
                    reader.stop()
                    del self._readers["mic"]
                    self._last_restart["mic"] = now
                    self._start_reader("mic", is_app=False, target=device_name)
                    with self._state_lock:
                        self.reconnections += 1
                    self._add_warning(
                        f"Перезапущено захоплення мікрофона '{self.source.name}'."
                    )
        else:
            self._start_reader("mic", is_app=False, target=device_name)
            if self._had_disconnect:
                self._had_disconnect = False
                with self._state_lock:
                    self.reconnections += 1
                self._add_warning(
                    f"Мікрофон '{self.source.name}' знову підключено до запису."
                )

    def _write_to_ffmpeg(self, payload: bytes) -> bool:
        proc = self.ffmpeg_proc
        if proc is None or proc.stdin is None or proc.poll() is not None:
            return False
        try:
            proc.stdin.write(payload)
            proc.stdin.flush()
            return True
        except (BrokenPipeError, OSError) as e:
            logger.error("FFmpeg stdin write failed for '%s': %s", self.source.name, e)
            self.ffmpeg_error = str(e)
            return False

    def _run_loop(self):
        last_sync = time.monotonic()
        tick_index = 0

        while not self._stop_event.is_set():
            now = time.monotonic()
            if now - last_sync >= 0.25:
                self._sync_readers(initial=False)
                last_sync = now

            if self.ffmpeg_proc is not None and self.ffmpeg_proc.poll() is not None:
                if self.ffmpeg_proc.returncode != 0:
                    tail = " | ".join(list(self._ffmpeg_stderr)[-3:])
                    self.ffmpeg_error = tail or f"FFmpeg exited early with code {self.ffmpeg_proc.returncode}"
                    self._add_warning(f"Помилка кодування '{self.source.name}': {self.ffmpeg_error}")
                break

            readers = list(self._readers.values())
            frames: List[bytes] = []
            max_q_len = 0
            for reader in readers:
                q_len = reader.queue_len()
                if q_len > max_q_len:
                    max_q_len = q_len
                frame = reader.pop_frame()
                if frame is not None:
                    frames.append(frame)

            elapsed = max(0.0, now - self.start_monotonic)
            expected_bytes = int(elapsed / self.tick_secs) * self.frame_bytes

            if frames:
                mixed = mix_pcm_s16le_frames(frames)
                if not self._write_to_ffmpeg(mixed):
                    break
                self.written_bytes += len(mixed)

                # Prevent latency drift if a single reader buffered ahead
                if len(readers) == 1 and max_q_len > 6:
                    extra = readers[0].pop_frame()
                    if extra is not None:
                        if not self._write_to_ffmpeg(extra):
                            break
                        self.written_bytes += len(extra)
            else:
                any_recent_data = any(
                    reader.last_data_monotonic > 0.0 and (now - reader.last_data_monotonic) < 0.08
                    for reader in readers
                )
                if any_recent_data and (expected_bytes - self.written_bytes) < (4 * self.frame_bytes):
                    pass  # Absorb PipeWire quantum jitter without false silence clicks
                else:
                    while self.written_bytes + self.frame_bytes <= expected_bytes:
                        if not self._write_to_ffmpeg(self.zero_frame):
                            break
                        self.written_bytes += self.frame_bytes

            tick_index += 1
            next_tick = self.start_monotonic + (tick_index * self.tick_secs)
            sleep_for = next_tick - time.monotonic()
            if sleep_for > 0:
                self._stop_event.wait(timeout=sleep_for)

    def stop(self):
        self._stop_event.set()
        if self._feeder_thread and self._feeder_thread.is_alive():
            self._feeder_thread.join(timeout=2.0)

        # Drain any remaining buffered frames and stop all sub-stream readers cleanly
        final_frames: List[bytes] = []
        for reader in list(self._readers.values()):
            f = reader.pop_frame()
            if f is not None:
                final_frames.append(f)
            reader.stop()
        self._readers.clear()

        if final_frames and self.ffmpeg_proc and self.ffmpeg_proc.poll() is None:
            mixed = mix_pcm_s16le_frames(final_frames)
            if self._write_to_ffmpeg(mixed):
                self.written_bytes += len(mixed)

        # Ensure FFmpeg never gets 0 bytes on stdin (so headered files finalize cleanly)
        if self.written_bytes == 0 and self.ffmpeg_proc and self.ffmpeg_proc.poll() is None:
            if self._write_to_ffmpeg(self.zero_frame):
                self.written_bytes += len(self.zero_frame)

        # Clean EOF shutdown for FFmpeg (never SIGINT immediately)
        proc = self.ffmpeg_proc
        if proc is not None:
            if proc.stdin is not None:
                try:
                    proc.stdin.close()
                except Exception:
                    pass

            if proc.poll() is None:
                try:
                    proc.wait(timeout=10.0)
                except subprocess.TimeoutExpired:
                    logger.warning("FFmpeg did not exit on EOF for '%s'; terminating...", self.source.name)
                    try:
                        proc.terminate()
                        proc.wait(timeout=2.0)
                    except subprocess.TimeoutExpired:
                        try:
                            proc.kill()
                            proc.wait(timeout=1.0)
                        except Exception:
                            pass
                    except Exception:
                        pass

            if self._ffmpeg_stderr_thread and self._ffmpeg_stderr_thread.is_alive():
                self._ffmpeg_stderr_thread.join(timeout=0.5)
            if proc.stderr is not None:
                try:
                    proc.stderr.close()
                except Exception:
                    pass

            if proc.returncode not in (0, None):
                tail = " | ".join(list(self._ffmpeg_stderr)[-4:])
                self.ffmpeg_error = tail or f"FFmpeg exited with code {proc.returncode}"
                logger.error("FFmpeg error for '%s': %s", self.source.name, self.ffmpeg_error)


class AudioRecorder:
    def __init__(self, monitor: Optional[Any] = None):
        self.monitor = monitor or audio_monitor
        self.current_session: Optional[RecordingSession] = None
        self._workers: List[ResilientSourceCaptureWorker] = []
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
                "reconnections": 0,
                "warnings": [],
                "session": None,
            }

        duration = 0.0
        if self.current_session.start_time:
            if self.current_session.status == "recording":
                duration = time.time() - self.current_session.start_time
            else:
                duration = self.current_session.duration_secs

        if self.current_session.status == "recording":
            reconnections = sum(w.reconnections for w in self._workers)
            warnings: List[str] = []
            for w in self._workers:
                with w._state_lock:
                    warnings.extend(w.warnings)
        else:
            reconnections = self.current_session.reconnections
            warnings = list(self.current_session.warnings)

        return {
            "status": self.current_session.status,
            "is_recording": self.current_session.status == "recording",
            "duration_secs": round(duration, 1),
            "reconnections": reconnections,
            "warnings": warnings,
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

        deps = check_audio_dependencies()
        if not deps["ready"]:
            missing = [k for k in ("parec", "ffmpeg") if not deps[k]]
            return False, None, f"Відсутні системні утиліти для запису: {', '.join(missing)}"

        cfg = config or settings_manager.config
        output_dir = Path(cfg.output_dir).expanduser()
        output_dir.mkdir(parents=True, exist_ok=True)

        sources_dict = self.monitor.get_sources()
        all_sources = sources_dict.get("apps", []) + sources_dict.get("mics", [])
        sources_by_id = {s["id"]: s for s in all_sources}

        selected_sources: List[AudioSource] = []
        seen_ids = set()
        for sid in source_ids:
            if sid in sources_by_id and sid not in seen_ids:
                seen_ids.add(sid)
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
                        device_name=s_data.get("device_name"),
                        stream_count=s_data.get("stream_count", 1),
                        is_bluetooth=s_data.get("is_bluetooth", False),
                        stream_sinks=s_data.get("stream_sinks", {}),
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
        self.monitor.set_recording_active(True)
        session_start_mono = time.monotonic()

        if cfg.mode == "multi_stem":
            session_folder = output_dir / session_id
            session_folder.mkdir(parents=True, exist_ok=True)

            for idx, src in enumerate(selected_sources, 1):
                clean_name = sanitize_filename(src.name)
                stem_file = session_folder / f"{idx:02d}_{clean_name}.{cfg.format}"
                worker = ResilientSourceCaptureWorker(
                    source=src,
                    output_path=stem_file,
                    config=cfg,
                    monitor=self.monitor,
                    session_start_monotonic=session_start_mono,
                )
                self._workers.append(worker)
                self.current_session.output_files.append(str(stem_file))
                worker.start()
        else:
            if len(selected_sources) == 1:
                src = selected_sources[0]
                clean_name = sanitize_filename(src.name)
                final_file = output_dir / f"{session_id}_{clean_name}.{cfg.format}"
                worker = ResilientSourceCaptureWorker(
                    source=src,
                    output_path=final_file,
                    config=cfg,
                    monitor=self.monitor,
                    session_start_monotonic=session_start_mono,
                )
                self._workers.append(worker)
                self.current_session.output_files.append(str(final_file))
                worker.start()
            else:
                temp_folder = output_dir / f".tmp_{session_id}"
                temp_folder.mkdir(parents=True, exist_ok=True)
                for idx, src in enumerate(selected_sources, 1):
                    temp_stem = temp_folder / f"stem_{idx}.wav"
                    temp_cfg = cfg.clone(format="wav", mode="single_mix")
                    worker = ResilientSourceCaptureWorker(
                        source=src,
                        output_path=temp_stem,
                        config=temp_cfg,
                        monitor=self.monitor,
                        session_start_monotonic=session_start_mono,
                    )
                    self._workers.append(worker)
                    self._temp_stem_files.append(temp_stem)
                    worker.start()

                final_mix_file = output_dir / f"{session_id}_mix.{cfg.format}"
                self.current_session.output_files.append(str(final_mix_file))

        logger.info(
            "Recording session %s started with %d resilient source workers.",
            session_id,
            len(self._workers),
        )
        return True, self.current_session, ""

    def stop_recording(self) -> Tuple[bool, Optional[RecordingSession], str]:
        if not self.is_recording or not self.current_session:
            return False, None, "No active recording session to stop"

        session = self.current_session
        session.status = "finalizing"
        session.duration_secs = time.time() - (session.start_time or time.time())

        ffmpeg_errors: List[str] = []
        try:
            for worker in self._workers:
                worker.stop()
                session.reconnections += worker.reconnections
                with worker._state_lock:
                    session.warnings.extend(worker.warnings)
                if worker.ffmpeg_error:
                    ffmpeg_errors.append(f"{worker.source.name}: {worker.ffmpeg_error}")
            self._workers.clear()
        finally:
            self.monitor.set_recording_active(False)

        if ffmpeg_errors:
            session.warnings.extend(ffmpeg_errors)

        # Perform mixdown if single_mix from multiple temp stems
        if session.config.mode == "single_mix" and len(self._temp_stem_files) > 1:
            temp_folder = self._temp_stem_files[0].parent
            valid_stems = [
                f for f in self._temp_stem_files
                if f.exists() and f.stat().st_size > 44
            ]
            if not valid_stems:
                self._temp_stem_files.clear()
                session.status = "error"
                session.error_message = (
                    f"Не вдалося записати жодної аудіодоріжки (сирі файли у {temp_folder})."
                )
                return False, session, session.error_message

            try:
                final_output = Path(session.output_files[0])
                mix_cmd = build_ffmpeg_mix_cmd(valid_stems, session.config, final_output)
                logger.info("Mixing %d tracks into %s", len(valid_stems), final_output)
                res = subprocess.run(
                    mix_cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                mix_ok = (
                    res.returncode == 0
                    and final_output.exists()
                    and final_output.stat().st_size > 0
                )
                if not mix_ok:
                    stderr_tail = " | ".join((res.stderr or "").strip().splitlines()[-3:])
                    self._temp_stem_files.clear()
                    session.status = "error"
                    session.error_message = (
                        f"Помилка зведення (сирі доріжки збережено у {temp_folder}): "
                        f"{stderr_tail or f'exit code {res.returncode}'}"
                    )
                    logger.error(session.error_message)
                    return False, session, session.error_message

                # Mixdown succeeded: remove temporary stems and folder
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
                self._temp_stem_files.clear()
                session.status = "error"
                session.error_message = (
                    f"Помилка зведення (сирі доріжки збережено у {temp_folder}): {e}"
                )
                logger.error(session.error_message)
                return False, session, session.error_message

        # Verify output files
        total_bytes = 0
        for fpath in session.output_files:
            p = Path(fpath)
            if p.exists():
                total_bytes += p.stat().st_size

        session.total_bytes = total_bytes
        if total_bytes == 0 and ffmpeg_errors:
            session.status = "error"
            session.error_message = "; ".join(ffmpeg_errors)
            return False, session, session.error_message

        session.status = "completed"
        logger.info(
            "Recording session %s completed: %d bytes written (reconnections=%d).",
            session.session_id,
            total_bytes,
            session.reconnections,
        )
        return True, session, ""


# Global singleton recorder instance
audio_recorder = AudioRecorder()

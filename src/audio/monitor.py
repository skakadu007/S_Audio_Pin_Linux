import time
import threading
import logging
import subprocess
import struct
from typing import Dict, List, Optional, Tuple, Any
import pulsectl

from ..models.audio import AudioSource
from .process_info import extract_process_info, format_microphone_name

logger = logging.getLogger("s_audio_pin.monitor")


class StreamPeakWorker:
    """
    Persistent, long-lived background audio worker for a single stream index or mic device.
    Runs a single persistent low-latency parec stream (16kHz mono) to continuously compute
    peak amplitudes without creating and destroying audio graph nodes in a loop.
    """
    def __init__(self, is_app: bool, target: str, sample_rate: int = 16000):
        self.is_app = is_app
        self.target = str(target)
        self.sample_rate = sample_rate
        self.peak = 0.0
        self._raw_peak = 0.0
        self.running = True
        self.proc: Optional[subprocess.Popen] = None
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self):
        if self.is_app:
            cmd = [
                "parec",
                f"--monitor-stream={self.target}",
                "--format=s16le",
                f"--rate={self.sample_rate}",
                "--channels=1",
                "--latency-msec=30",
            ]
        else:
            cmd = [
                "parec",
                "-d", str(self.target),
                "--format=s16le",
                f"--rate={self.sample_rate}",
                "--channels=1",
                "--latency-msec=30",
            ]

        try:
            self.proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                bufsize=1024 * 4,
            )
            # Read ~40ms chunks (640 samples * 2 bytes = 1280 bytes)
            chunk_bytes = int(self.sample_rate * 0.04 * 2)

            while self.running and self.proc and self.proc.poll() is None:
                raw = self.proc.stdout.read(chunk_bytes)
                if not raw:
                    break
                sample_count = len(raw) // 2
                if sample_count > 0:
                    shorts = struct.unpack(f"{sample_count}h", raw[:sample_count * 2])
                    val = max(abs(s) for s in shorts) / 32768.0
                    self._raw_peak = val
                    # Smooth peak with fast rise and decay
                    if val >= self.peak:
                        self.peak = val
                    else:
                        self.peak = max(0.0, self.peak * 0.85)

        except Exception as e:
            logger.debug(f"StreamPeakWorker error for target={self.target}: {e}")
        finally:
            self.stop()

    def stop(self):
        self.running = False
        if self.proc and self.proc.poll() is None:
            try:
                self.proc.terminate()
            except Exception:
                pass


class AudioMonitor:
    def __init__(self, client_name: str = "s-audio-pin-monitor"):
        self.client_name = client_name
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

        # Cached sources and persistent workers
        self._apps: Dict[str, AudioSource] = {}
        self._mics: Dict[str, AudioSource] = {}
        self._peaks: Dict[str, float] = {}

        # Persistent workers: worker_key -> StreamPeakWorker
        self._workers: Dict[str, StreamPeakWorker] = {}

        # Callback for WebSocket or UI notification
        self.on_update_callback = None

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._discovery_loop, daemon=True)
        self._thread.start()
        logger.info("AudioMonitor persistent discovery thread started.")

    def stop(self):
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)

        # Stop all persistent workers cleanly
        with self._lock:
            for worker in self._workers.values():
                worker.stop()
            self._workers.clear()

        logger.info("AudioMonitor stopped and all stream workers cleaned up.")

    @staticmethod
    def _apply_decay(prev_peak: float, new_peak: float, decay_rate: float = 0.85) -> float:
        """
        Fast rise, smooth exponential falloff for natural VU meter physics.
        """
        if new_peak >= prev_peak:
            return new_peak
        return max(0.0, prev_peak * decay_rate)

    def get_sources(self) -> Dict[str, List[Dict[str, Any]]]:
        with self._lock:
            return {
                "apps": [app.to_dict() for app in self._apps.values()],
                "mics": [mic.to_dict() for mic in self._mics.values()],
            }

    def get_peaks(self) -> Dict[str, float]:
        with self._lock:
            # Update peak dictionary from active workers in O(1) time
            peaks: Dict[str, float] = {}
            for app_id, app in self._apps.items():
                app_peak = 0.0
                for s_idx in app.stream_indices:
                    w_key = f"app:{s_idx}"
                    if w_key in self._workers:
                        app_peak = max(app_peak, self._workers[w_key].peak)
                peaks[app_id] = app_peak

            for mic_id, mic in self._mics.items():
                w_key = f"mic:{mic.device_name or mic.index}"
                if w_key in self._workers:
                    peaks[mic_id] = self._workers[w_key].peak
                else:
                    peaks[mic_id] = 0.0

            self._peaks = peaks
            return dict(peaks)

    def _discovery_loop(self):
        """
        Runs at a relaxed interval (500ms - 1000ms) to scan for new/closed applications
        and devices, keeping persistent workers in sync without spamming the PipeWire audio graph.
        """
        pulse: Optional[pulsectl.Pulse] = None

        while self._running:
            try:
                if pulse is None:
                    pulse = pulsectl.Pulse(self.client_name)

                # 1. Scan sink inputs (Active audio applications)
                raw_sink_inputs = pulse.sink_input_list()
                grouped_apps: Dict[str, Dict[str, Any]] = {}
                active_app_stream_indices = set()

                for si in raw_sink_inputs:
                    # Ignore unlinked/floating sink inputs (e.g. Viber idle sound slots with sink = 4294967295)
                    if si.sink is None or si.sink == 4294967295 or si.sink < 0:
                        continue

                    active_app_stream_indices.add(si.index)
                    display_name, proc_name, pid, icon_name = extract_process_info(si.proplist)

                    # Group key by PID or process name
                    if pid:
                        group_key = f"app:pid_{pid}"
                    elif proc_name:
                        group_key = f"app:proc_{proc_name}"
                    else:
                        group_key = f"app:name_{display_name}"

                    rate_val = getattr(si.sample_spec, "rate", 48000) if hasattr(si, "sample_spec") and si.sample_spec else 48000
                    if not rate_val:
                        rate_val = 48000

                    if group_key not in grouped_apps:
                        grouped_apps[group_key] = {
                            "id": group_key,
                            "type": "app",
                            "primary_index": si.index,
                            "stream_indices": [si.index],
                            "name": display_name,
                            "process_name": proc_name,
                            "pid": pid,
                            "icon_name": icon_name,
                            "channels": si.channel_count if si.channel_count else 2,
                            "sample_rate": rate_val,
                            "volume": float(si.volume.value_flat),
                            "is_muted": bool(si.mute),
                        }
                    else:
                        entry = grouped_apps[group_key]
                        entry["stream_indices"].append(si.index)
                        entry["channels"] = max(entry["channels"], si.channel_count or 2)
                        if not entry["pid"] and pid:
                            entry["pid"] = pid
                        if not entry["icon_name"] and icon_name:
                            entry["icon_name"] = icon_name

                # Build finalized AudioSource models
                current_apps: Dict[str, AudioSource] = {}
                for group_key, data in grouped_apps.items():
                    current_apps[group_key] = AudioSource(
                        id=group_key,
                        type="app",
                        index=data["primary_index"],
                        name=data["name"],
                        process_name=data["process_name"],
                        pid=data["pid"],
                        icon_name=data["icon_name"],
                        channels=data["channels"],
                        sample_rate=data["sample_rate"],
                        volume=data["volume"],
                        is_muted=data["is_muted"],
                        peak_level=0.0,
                        stream_indices=data["stream_indices"],
                        stream_count=len(data["stream_indices"]),
                    )

                # Ensure persistent workers for each active app stream
                for s_idx in active_app_stream_indices:
                    w_key = f"app:{s_idx}"
                    if w_key not in self._workers:
                        self._workers[w_key] = StreamPeakWorker(is_app=True, target=str(s_idx))

                # 2. Scan physical microphones
                raw_sources = pulse.source_list()
                current_mics: Dict[str, AudioSource] = {}
                active_mic_devices = set()

                for src in raw_sources:
                    # Skip monitor sources of output sinks
                    if src.name.endswith(".monitor") or getattr(src, "monitor_of_sink", None) not in (None, 4294967295, -1):
                        continue

                    source_id = f"source:{src.index}"
                    friendly_name = format_microphone_name(src)
                    device_name = src.name
                    active_mic_devices.add(device_name)

                    # Ensure persistent worker for this physical mic
                    w_key = f"mic:{device_name}"
                    if w_key not in self._workers:
                        self._workers[w_key] = StreamPeakWorker(is_app=False, target=device_name)

                    current_mics[source_id] = AudioSource(
                        id=source_id,
                        type="mic",
                        index=src.index,
                        name=friendly_name,
                        channels=src.channel_count,
                        sample_rate=src.sample_spec.rate,
                        volume=float(src.volume.value_flat),
                        is_muted=bool(src.mute),
                        peak_level=0.0,
                        stream_indices=[src.index],
                        device_name=device_name,
                    )

                # Clean up workers for closed streams and disconnected devices
                for w_key in list(self._workers.keys()):
                    if w_key.startswith("app:"):
                        s_idx = int(w_key.split("app:")[1])
                        if s_idx not in active_app_stream_indices:
                            self._workers[w_key].stop()
                            del self._workers[w_key]
                    elif w_key.startswith("mic:"):
                        dev = w_key.split("mic:")[1]
                        if dev not in active_mic_devices:
                            self._workers[w_key].stop()
                            del self._workers[w_key]

                # Update internal state safely
                with self._lock:
                    self._apps = current_apps
                    self._mics = current_mics

                time.sleep(0.8)  # Relaxed 800ms discovery poll - zero CPU overhead

            except Exception as e:
                logger.warning(f"PulseAudio discovery loop error: {e}. Reconnecting in 1s...")
                if pulse:
                    try:
                        pulse.close()
                    except Exception:
                        pass
                    pulse = None
                time.sleep(1.0)

        if pulse:
            try:
                pulse.close()
            except Exception:
                pass


# Global singleton monitor
audio_monitor = AudioMonitor()

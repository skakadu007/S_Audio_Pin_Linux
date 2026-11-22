import logging
import re
import struct
import subprocess
import threading
import time
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple
import pulsectl

from ..models.audio import AudioSource
from .process_info import (
    extract_process_info,
    format_microphone_name,
    is_bluetooth_source,
    make_app_group_key,
)

logger = logging.getLogger("s_audio_pin.monitor")

_BT_MAC_RE = re.compile(r"([0-9a-fA-F]{2}(?:[_:][0-9a-fA-F]{2}){5})")


def _bt_device_identity(device_name: Optional[str]) -> Optional[str]:
    """Extracts Bluetooth MAC or bluez base identity so a BT device can match across profile changes."""
    if not device_name:
        return None
    m = _BT_MAC_RE.search(device_name)
    if m:
        return m.group(1).replace(":", "_").lower()
    if "bluez" in device_name.lower():
        parts = device_name.split(".")
        if len(parts) >= 2:
            return parts[1].lower()
    return None


class StreamPeakWorker:
    """
    Persistent, long-lived background audio worker for a single stream index or wired mic device.
    Runs a low-latency parec stream (16kHz mono) to continuously compute peak amplitudes.
    """

    def __init__(
        self,
        is_app: bool,
        target: str,
        sample_rate: int = 16000,
        sink_id: Optional[int] = None,
    ):
        self.is_app = is_app
        self.target = str(target)
        self.sample_rate = sample_rate
        self.sink_id = sink_id
        self.peak = 0.0
        self._raw_peak = 0.0
        self.running = True
        self._proc_lock = threading.Lock()
        self.proc: Optional[subprocess.Popen] = None
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def is_alive(self) -> bool:
        """Returns True if the worker thread and underlying parec process are still active."""
        if not self.running or not self.thread.is_alive():
            return False
        with self._proc_lock:
            if self.proc is not None and self.proc.poll() is not None:
                return False
        return True

    def _run(self):
        base_cmd = [
            "parec",
            "--client-name=s-audio-pin-monitor",
            "--stream-name=peak-monitor",
            "--format=s16le",
            f"--rate={self.sample_rate}",
            "--channels=1",
            "--latency-msec=30",
        ]
        if self.is_app:
            cmd = base_cmd + [f"--monitor-stream={self.target}"]
        else:
            cmd = base_cmd + ["-d", str(self.target)]

        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                bufsize=1024 * 4,
            )
            with self._proc_lock:
                if not self.running:
                    try:
                        proc.terminate()
                        proc.wait(timeout=0.5)
                    except Exception:
                        try:
                            proc.kill()
                            proc.wait(timeout=0.5)
                        except Exception:
                            pass
                    return
                self.proc = proc

            # Read ~40ms chunks (640 samples * 2 bytes = 1280 bytes)
            chunk_bytes = int(self.sample_rate * 0.04 * 2)

            while self.running and proc.poll() is None:
                if proc.stdout is None:
                    break
                raw = proc.stdout.read(chunk_bytes)
                if not raw:
                    break
                sample_count = len(raw) // 2
                if sample_count > 0:
                    shorts = struct.unpack(f"{sample_count}h", raw[: sample_count * 2])
                    val = max(abs(s) for s in shorts) / 32768.0
                    self._raw_peak = val
                    if val >= self.peak:
                        self.peak = val
                    else:
                        self.peak = max(0.0, self.peak * 0.85)

        except Exception as e:
            logger.debug("StreamPeakWorker error for target=%s: %s", self.target, e)
        finally:
            self.running = False
            self._reap_proc()

    def _reap_proc(self):
        with self._proc_lock:
            proc = self.proc
            self.proc = None

        if proc is None:
            return

        if proc.poll() is None:
            try:
                proc.terminate()
                proc.wait(timeout=0.5)
            except subprocess.TimeoutExpired:
                try:
                    proc.kill()
                    proc.wait(timeout=0.5)
                except Exception:
                    pass
            except Exception:
                pass
        else:
            try:
                proc.wait(timeout=0.1)
            except Exception:
                pass

        if proc.stdout is not None:
            try:
                proc.stdout.close()
            except Exception:
                pass

    def stop(self):
        self.running = False
        self._reap_proc()


class AudioMonitor:
    def __init__(self, client_name: str = "s-audio-pin-monitor"):
        self.client_name = client_name
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._wake_event = threading.Event()

        # Cached sources and persistent workers
        self._apps: Dict[str, AudioSource] = {}
        self._mics: Dict[str, AudioSource] = {}
        self._peaks: Dict[str, float] = {}

        # Persistent workers: worker_key -> StreamPeakWorker
        self._workers: Dict[str, StreamPeakWorker] = {}

        # Monitored mic IDs (only armed non-Bluetooth mics open parec peak workers)
        self._monitored_mic_ids: Set[str] = set()
        self._recording_active = False
        self._pulse_connected = False

        self.on_update_callback = None

    @property
    def pulse_connected(self) -> bool:
        with self._lock:
            return self._pulse_connected

    def start(self):
        if self._running:
            return
        self._running = True
        self._wake_event.clear()
        self._thread = threading.Thread(target=self._discovery_loop, daemon=True)
        self._thread.start()
        logger.info("AudioMonitor persistent discovery thread started.")

    def stop(self):
        self._running = False
        self._wake_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.5)

        with self._lock:
            workers_to_stop = list(self._workers.values())
            self._workers.clear()
            self._pulse_connected = False

        for worker in workers_to_stop:
            worker.stop()

        logger.info("AudioMonitor stopped and all stream workers cleaned up.")

    @staticmethod
    def _apply_decay(prev_peak: float, new_peak: float, decay_rate: float = 0.85) -> float:
        """Fast rise, smooth exponential falloff for natural VU meter physics."""
        if new_peak >= prev_peak:
            return new_peak
        return max(0.0, prev_peak * decay_rate)

    def set_recording_active(self, active: bool):
        with self._lock:
            self._recording_active = bool(active)
        self._wake_event.set()

    def set_monitored_mics(self, source_ids: Iterable[str]):
        """
        Updates which microphones are armed/selected.
        Unarmed microphones and Bluetooth microphones never keep active parec peak streams,
        preventing PipeWire/WirePlumber from forcing Bluetooth A2DP -> HFP profile switches.
        """
        new_ids = {str(sid) for sid in source_ids if sid}
        workers_to_stop: List[StreamPeakWorker] = []

        with self._lock:
            self._monitored_mic_ids = new_ids
            allowed_mic_devices = {
                mic.device_name
                for mic_id, mic in self._mics.items()
                if mic_id in new_ids and not mic.is_bluetooth and mic.device_name
            }
            for w_key in list(self._workers.keys()):
                if w_key.startswith("mic:"):
                    dev = w_key[4:]
                    if dev not in allowed_mic_devices:
                        workers_to_stop.append(self._workers.pop(w_key))

        for worker in workers_to_stop:
            worker.stop()

        self._wake_event.set()

    def get_sources(self) -> Dict[str, List[Dict[str, Any]]]:
        with self._lock:
            return {
                "apps": [app.to_dict() for app in self._apps.values()],
                "mics": [mic.to_dict() for mic in self._mics.values()],
            }

    def get_peaks(self) -> Dict[str, float]:
        with self._lock:
            peaks: Dict[str, float] = {}
            for app_id, app in self._apps.items():
                app_peak = 0.0
                for s_idx in app.stream_indices:
                    w_key = f"app:{s_idx}"
                    worker = self._workers.get(w_key)
                    if worker is not None and worker.is_alive():
                        app_peak = max(app_peak, worker.peak)
                peaks[app_id] = app_peak

            for mic_id, mic in self._mics.items():
                w_key = f"mic:{mic.device_name or mic.index}"
                worker = self._workers.get(w_key)
                if worker is not None and worker.is_alive():
                    peaks[mic_id] = worker.peak
                else:
                    peaks[mic_id] = 0.0

            self._peaks = peaks
            return dict(peaks)

    def get_live_streams_for_source(self, source: AudioSource) -> Dict[str, Any]:
        """
        Thread-safe lookup returning live PipeWire/PulseAudio stream indices (for apps)
        or live device_name (for mics), resilient to stream/sink/BT profile switches.
        """
        with self._lock:
            if source.type == "app":
                matched: Optional[AudioSource] = self._apps.get(source.id)

                if matched is None and source.process_name:
                    proc_low = source.process_name.lower()
                    for app in self._apps.values():
                        if app.process_name and app.process_name.lower() == proc_low:
                            matched = app
                            break

                if matched is None and source.pid:
                    for app in self._apps.values():
                        if app.pid == source.pid:
                            matched = app
                            break

                if matched is None and source.name:
                    for app in self._apps.values():
                        if app.name == source.name:
                            matched = app
                            break

                if matched is None:
                    return {"streams": [], "found": False}

                indices = matched.stream_indices or [matched.index]
                streams = [(idx, matched.stream_sinks.get(idx)) for idx in indices]
                return {"streams": streams, "found": True}

            # Microphone lookup
            matched_mic: Optional[AudioSource] = None
            if source.device_name:
                for mic in self._mics.values():
                    if mic.device_name == source.device_name:
                        matched_mic = mic
                        break

            if matched_mic is None:
                matched_mic = self._mics.get(source.id)

            if matched_mic is None and (source.is_bluetooth or "bluez" in (source.device_name or "").lower()):
                src_bt_id = _bt_device_identity(source.device_name)
                for mic in self._mics.values():
                    if mic.is_bluetooth:
                        mic_bt_id = _bt_device_identity(mic.device_name)
                        if src_bt_id and mic_bt_id and src_bt_id == mic_bt_id:
                            matched_mic = mic
                            break
                if matched_mic is None and source.name:
                    for mic in self._mics.values():
                        if mic.is_bluetooth and mic.name == source.name:
                            matched_mic = mic
                            break

            if matched_mic is None or not matched_mic.device_name:
                return {"device_name": None, "found": False}

            return {"device_name": matched_mic.device_name, "found": True}

    def _create_worker(
        self,
        is_app: bool,
        target: str,
        sink_id: Optional[int] = None,
    ) -> StreamPeakWorker:
        return StreamPeakWorker(is_app=is_app, target=target, sink_id=sink_id)

    def _process_snapshot(self, raw_sink_inputs: List[Any], raw_sources: List[Any]) -> None:
        """
        Reconciles active apps, microphones, and peak workers from a PulseAudio snapshot.
        """
        grouped_apps: Dict[str, Dict[str, Any]] = {}
        active_app_sinks: Dict[int, Optional[int]] = {}

        for si in raw_sink_inputs:
            # Ignore unlinked/floating sink inputs (e.g. idle slots with sink = 4294967295)
            if si.sink is None or si.sink == 4294967295 or si.sink < 0:
                continue

            proplist = getattr(si, "proplist", {}) or {}
            raw_app_name = str(proplist.get("application.name", "") or "").lower()
            raw_proc_bin = str(proplist.get("application.process.binary", "") or "").lower()
            if raw_app_name.startswith("s-audio-pin") or raw_app_name.startswith("s_audio_pin"):
                continue
            if raw_proc_bin.startswith("s-audio-pin") or raw_proc_bin.startswith("s_audio_pin"):
                continue

            active_app_sinks[si.index] = si.sink
            display_name, proc_name, pid, icon_name = extract_process_info(proplist)
            group_key = make_app_group_key(display_name, proc_name, pid)

            sample_spec = getattr(si, "sample_spec", None)
            rate_val = getattr(sample_spec, "rate", 48000) if sample_spec else 48000
            if not rate_val:
                rate_val = 48000

            ch_count = getattr(si, "channel_count", 2) or 2
            vol_obj = getattr(si, "volume", None)
            vol_val = float(getattr(vol_obj, "value_flat", 1.0)) if vol_obj else 1.0
            is_muted = bool(getattr(si, "mute", False))

            if group_key not in grouped_apps:
                grouped_apps[group_key] = {
                    "id": group_key,
                    "type": "app",
                    "primary_index": si.index,
                    "stream_indices": [si.index],
                    "stream_sinks": {si.index: si.sink},
                    "name": display_name,
                    "process_name": proc_name,
                    "pid": pid,
                    "icon_name": icon_name,
                    "channels": ch_count,
                    "sample_rate": rate_val,
                    "volume": vol_val,
                    "is_muted": is_muted,
                }
            else:
                entry = grouped_apps[group_key]
                entry["stream_indices"].append(si.index)
                entry["stream_sinks"][si.index] = si.sink
                entry["channels"] = max(entry["channels"], ch_count)
                if not entry["pid"] and pid:
                    entry["pid"] = pid
                if not entry["icon_name"] and icon_name:
                    entry["icon_name"] = icon_name

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
                stream_sinks=data["stream_sinks"],
            )

        current_mics: Dict[str, AudioSource] = {}
        wired_mic_devices: Dict[str, str] = {}  # source_id -> device_name

        for src in raw_sources:
            src_name = getattr(src, "name", "") or ""
            monitor_of = getattr(src, "monitor_of_sink", None)
            if src_name.endswith(".monitor") or monitor_of not in (None, 4294967295, -1):
                continue

            source_id = f"source:{src.index}"
            friendly_name = format_microphone_name(src)
            bt = is_bluetooth_source(src)
            sample_spec = getattr(src, "sample_spec", None)
            rate_val = getattr(sample_spec, "rate", 48000) if sample_spec else 48000
            if not rate_val:
                rate_val = 48000
            ch_count = getattr(src, "channel_count", 1) or 1
            vol_obj = getattr(src, "volume", None)
            vol_val = float(getattr(vol_obj, "value_flat", 1.0)) if vol_obj else 1.0

            current_mics[source_id] = AudioSource(
                id=source_id,
                type="mic",
                index=src.index,
                name=friendly_name,
                channels=ch_count,
                sample_rate=rate_val,
                volume=vol_val,
                is_muted=bool(getattr(src, "mute", False)),
                peak_level=0.0,
                stream_indices=[src.index],
                device_name=src_name,
                is_bluetooth=bt,
            )

            if not bt and src_name:
                wired_mic_devices[source_id] = src_name

        workers_to_stop: List[StreamPeakWorker] = []
        to_spawn: List[Tuple[str, bool, str, Optional[int]]] = []

        with self._lock:
            monitored_ids = set(self._monitored_mic_ids)
            active_monitored_mic_devs = {
                dev
                for sid, dev in wired_mic_devices.items()
                if sid in monitored_ids
            }

            # Reconcile existing workers: remove closed, dead, or sink-changed workers
            for w_key in list(self._workers.keys()):
                worker = self._workers[w_key]
                if w_key.startswith("app:"):
                    s_idx = int(w_key[4:])
                    if (
                        s_idx not in active_app_sinks
                        or not worker.is_alive()
                        or worker.sink_id != active_app_sinks[s_idx]
                    ):
                        workers_to_stop.append(self._workers.pop(w_key))
                elif w_key.startswith("mic:"):
                    dev = w_key[4:]
                    if dev not in active_monitored_mic_devs or not worker.is_alive():
                        workers_to_stop.append(self._workers.pop(w_key))

            # Queue missing workers to spawn outside lock
            for s_idx, sink_id in active_app_sinks.items():
                w_key = f"app:{s_idx}"
                if w_key not in self._workers:
                    to_spawn.append((w_key, True, str(s_idx), sink_id))

            for dev in active_monitored_mic_devs:
                w_key = f"mic:{dev}"
                if w_key not in self._workers:
                    to_spawn.append((w_key, False, dev, None))

            self._apps = current_apps
            self._mics = current_mics

        # Stop obsolete/dead workers outside lock
        for worker in workers_to_stop:
            worker.stop()

        # Spawn new workers outside lock
        new_workers: Dict[str, StreamPeakWorker] = {}
        for w_key, is_app, target, sink_id in to_spawn:
            new_workers[w_key] = self._create_worker(is_app=is_app, target=target, sink_id=sink_id)

        if new_workers:
            with self._lock:
                for w_key, worker in new_workers.items():
                    if w_key not in self._workers:
                        self._workers[w_key] = worker
                    else:
                        worker.stop()

    def _discovery_loop(self):
        """
        Scans for new/closed applications and devices, keeping persistent peak workers in sync.
        Polls every 0.35s while recording (fast Bluetooth/sink switch recovery) and 0.8s when idle.
        """
        pulse: Optional[pulsectl.Pulse] = None

        while self._running:
            try:
                if pulse is None:
                    pulse = pulsectl.Pulse(self.client_name)
                    with self._lock:
                        self._pulse_connected = True

                raw_sink_inputs = pulse.sink_input_list()
                raw_sources = pulse.source_list()
                self._process_snapshot(raw_sink_inputs, raw_sources)

                with self._lock:
                    interval = 0.35 if self._recording_active else 0.8
                self._wake_event.wait(timeout=interval)
                self._wake_event.clear()

            except Exception as e:
                logger.warning("PulseAudio discovery loop error: %s. Reconnecting in 1s...", e)
                with self._lock:
                    self._pulse_connected = False
                if pulse:
                    try:
                        pulse.close()
                    except Exception:
                        pass
                    pulse = None
                self._wake_event.wait(timeout=1.0)
                self._wake_event.clear()

        if pulse:
            try:
                pulse.close()
            except Exception:
                pass


# Global singleton monitor
audio_monitor = AudioMonitor()

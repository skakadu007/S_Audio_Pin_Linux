# Technical Research & Architecture Decisions: S_Audio_Pin_Linux

**Feature**: Linux Application Audio Monitor & Multi-Source Pinpoint Recorder (`001-audio-pin-recorder`)
**Date**: 2026-08-24
**Status**: Completed

## 1. Audio Subsystem Integration & Discovery

### Decision
Use **PulseAudio Client API (via `libpulse` / `pulsectl`)** running seamlessly on **PipeWire & PulseAudio**.

### Rationale
- PipeWire on modern Linux distributions (Fedora, Ubuntu, Arch, Debian) provides 100% binary and protocol compatibility via `pipewire-pulse` / `libpulse`.
- `pulsectl` connects directly to the user's native pulse socket (`/run/user/$UID/pulse/native`), allowing real-time event-driven discovery of `sink-inputs` (applications emitting sound), client properties (`application.name`, `application.process.id`, `application.icon_name`, `media.name`), and `sources` (physical microphones).
- Zero administrative / root privileges required.

### Alternatives Considered
- *Direct PipeWire C API (`libpipewire`)*: High complexity, C FFI binding overhead, and less uniform cross-distro Python bindings compared to the stable PulseAudio protocol socket.
- *ALSA loopback kernel modules*: Requires root permissions, manual device configuration, and cannot isolate individual application processes.

---

## 2. Real-Time Per-Process Audio Level Metering (VU / Peak Meters)

### Decision
Implement a low-overhead, asynchronous peak monitoring stream using `pa_stream_peek` (via `pulsectl` Peak Detector / monitor streams) operating at 30-60 Hz.

### Rationale
- Peak detector streams return instantaneous peak/RMS amplitudes calculated directly by the audio server without transferring full high-bandwidth PCM streams over IPC for unselected applications.
- Provides sub-50ms visual responsiveness for VU meters while keeping CPU consumption under 2%.

### Alternatives Considered
- *Full PCM stream decoding for all apps in Python*: Excessive CPU and memory consumption when many apps or browser tabs are active.

---

## 3. Audio Recording & Encoding Pipeline

### Decision
Use asynchronous subprocess streams combining native `parec --monitor-stream=<sink_input_index>` and `parec -d <source_device>` piped into high-performance `ffmpeg` encoder instances.

### Rationale
- `parec --monitor-stream=<INDEX>` extracts the exact pristine PCM stream from a specific application sink-input directly from the audio server without capturing unwanted background sounds or desktop notifications.
- `parec -d <SOURCE>` captures microphone audio simultaneously.
- `ffmpeg` handles real-time encoding to **WAV (PCM s16le / s24le)** and **MP3 (libmp3lame)** with user-selectable bitrates (128k, 192k, 256k, 320k) with minimal latency and high fidelity.
- **Multitrack Mode (Separate Stems)**: Each selected process and microphone runs an isolated `parec | ffmpeg` worker writing to timestamped stem files (`App_PID_<name>.mp3`, `Mic_<name>.mp3`) in a unified session folder.
- **Master Mix Mode (Single File)**: Streams are fed into a synchronized `ffmpeg -filter_complex amix` pipeline producing a unified stereo mixdown file.

### Alternatives Considered
- *Pure Python audio mixing/encoding (wave/lameenc)*: Slower for real-time multi-stream mixing compared to hardware-optimized `ffmpeg` with `amix`.

---

## 4. UI Architecture & Desktop Experience

### Decision
A lightweight, modern Desktop UI powered by **FastAPI/WebSocket backend + sleek HTML5/CSS3/Vanilla JS frontend**, packaged and run seamlessly as a standalone desktop web app / local desktop client.

### Rationale
- Delivers rich aesthetics: sleek dark mode, glassmorphism, fluid SVG/Canvas VU peak meters, reactive switches, real-time animated recording timer, and instant download/open folder integration.
- True cross-desktop compatibility across Linux Wayland and X11 (GNOME, KDE, XFCE, Sway, Hyprland).
- Modular separation between the Audio Engine (Python/Pulse) and presentation layer.
- Ultra-lightweight memory footprint and instant startup.

### Alternatives Considered
- *Tkinter*: Lacks modern CSS styling, animated peak meters look dated and stutter.
- *Heavy Electron Bundle*: 200MB+ binary footprint and high RAM usage, violating the lightweight principle.

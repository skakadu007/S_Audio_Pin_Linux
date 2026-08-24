# Implementation Plan: Linux Application Audio Monitor & Multi-Source Recorder (S_Audio_Pin_Linux)

**Branch**: `001-audio-pin-recorder` | **Date**: 2026-08-24 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-audio-pin-recorder/spec.md`

## Summary

Build a lightweight, modern Linux desktop application that monitors running applications emitting sound, displays real-time audio VU/peak meters for each process, allows independent multi-selection of processes and microphone inputs, and records audio selectively into single mixdown or multitrack stems in configurable formats (WAV/MP3) with custom bitrates.

The solution utilizes **PulseAudio/PipeWire Client APIs (`pulsectl` / `libpulse`)** for stream monitoring and peak detection, asynchronous **`parec` + `ffmpeg` pipelines** for pristine isolated recording and encoding, and a modern **FastAPI/WebSocket backend + sleek HTML5/CSS3/Vanilla JS frontend** desktop user interface.

## Technical Context

**Language/Version**: Python 3.11+ (Runtime on Python 3.14.7)

**Primary Dependencies**: `pulsectl`, `psutil`, `fastapi`, `uvicorn`, `websockets`, `ffmpeg`, `parec` (PipeWire / PulseAudio)

**Storage**: Local filesystem storage for configuration (`~/.config/s_audio_pin/config.json`) and audio recordings (`~/Recordings/S_Audio_Pin/`)

**Testing**: `pytest`, mock pulse server harness, synthetic audio generation tests

**Target Platform**: Linux Desktop (Fedora, Ubuntu, Debian, Arch, etc. on PipeWire / PulseAudio, Wayland / X11)

**Project Type**: Desktop Application (Local Core Engine + Desktop Web/UI)

**Performance Goals**: Sub-50ms metering latency, 60fps UI visualizer rendering, <3% background CPU overhead, 0% audio buffer underruns

**Constraints**: Zero root/sudo permissions needed, isolated process stream capture without capturing unwanted desktop sounds, robust against process exit mid-recording

**Scale/Scope**: Real-time management of up to 50 concurrent process streams and multiple hardware microphone inputs

## Constitution Check

*GATE: All gates verified against `.specify/memory/constitution.md`.*

- [x] **I. Low-Latency & Resource Efficiency**: Event-driven stream discovery and low-bandwidth peak meters ensure CPU utilization <3%.
- [x] **II. Native Linux Audio Architecture**: Seamlessly targets PipeWire / PulseAudio via standard `/run/user/$UID/pulse/native` socket.
- [x] **III. Flexible & Synchronized Capture Fidelity**: Employs `parec --monitor-stream` + `ffmpeg` for sample-accurate multitrack stems and single master mixdown with configurable WAV/MP3 bitrates.
- [x] **IV. Modern, Fluid & Responsive UI**: Dedicated modern UI with dark aesthetics, glassmorphism, dynamic audio level canvas visualizers, and async non-blocking audio capture.
- [x] **V. Dynamic Robustness & Stream Safety**: Gracefully handles process termination mid-recording and atomic file writes.

## Project Structure

### Documentation (this feature)

```text
specs/001-audio-pin-recorder/
├── spec.md              # Feature specification
├── plan.md              # This implementation plan
├── research.md          # Technical architecture & research decisions
├── data-model.md        # Entities, schemas, and state transitions
├── contracts/           # API and WebSocket protocol contracts
│   └── api-contract.md
├── quickstart.md        # Validation scenarios and quickstart guide
├── checklists/          # Quality checklists
│   └── requirements.md
└── tasks.md             # Actionable implementation tasks (Phase 2)
```

### Source Code Layout

```text
src/
├── audio/
│   ├── __init__.py
│   ├── monitor.py       # PulseAudio/PipeWire sink-input & source discovery + peak meters
│   ├── recorder.py      # Multi-stream recording engine (parec + ffmpeg pipeline)
│   ├── encoder.py       # WAV / MP3 bitrate & mixdown configuration
│   └── process_info.py  # PID, process name, and desktop icon resolution
├── config/
│   ├── __init__.py
│   └── settings.py      # App settings & recording configuration persistence
├── server/
│   ├── __init__.py
│   ├── app.py           # FastAPI application & REST endpoints
│   └── ws.py            # High-frequency WebSocket level meter broadcaster
├── ui/
│   ├── index.html       # Modern desktop UI markup
│   ├── css/
│   │   └── style.css    # Premium dark theme styling, glassmorphism, responsive layout
│   └── js/
│       ├── app.js       # UI state, audio source selection, and recording controls
│       └── visualizer.js# Smooth 60fps Canvas VU / peak meter rendering engine
└── main.py              # Application entry point & launcher

tests/
├── unit/
│   ├── test_config.py   # Settings serialization and defaults
│   ├── test_process.py  # Process resolution & metadata
│   └── test_encoder.py  # FFmpeg command builder & format verification
├── integration/
│   ├── test_monitor.py  # Audio source discovery and monitoring
│   └── test_recorder.py # Multi-source recording pipeline
└── conftest.py          # Pytest fixtures and mock audio helpers
```

**Structure Decision**: Single project layout with clean separation of Audio Engine (`src/audio`), Backend Server (`src/server`), Configuration (`src/config`), and Presentation UI (`src/ui`).

## Complexity Tracking

*No constitution violations; architecture remains lightweight, direct, and modular.*

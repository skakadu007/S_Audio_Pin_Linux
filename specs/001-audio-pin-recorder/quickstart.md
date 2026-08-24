# Quickstart & Verification Guide: S_Audio_Pin_Linux

**Feature**: Linux Application Audio Monitor & Multi-Source Pinpoint Recorder (`001-audio-pin-recorder`)
**Date**: 2026-08-24
**Status**: Ready

## Prerequisites

- Linux operating system running PipeWire or PulseAudio audio daemon.
- Python 3.11+ installed.
- System utilities available: `ffmpeg`, `parec` (part of `pulseaudio-utils` / `pipewire-pulse`).
- Virtual environment created with dependencies (`pulsectl`, `psutil`, `fastapi`, `uvicorn`, `websockets`).

## Launching the Application

1. Activate virtual environment or run via `uv`:
   ```bash
   uv run python -m src.main
   ```
2. The application will start the backend engine and launch the modern desktop UI window / web client at `http://127.0.0.1:8765`.

---

## End-to-End Validation Scenarios

### Scenario 1: Audio Process Detection & Live VU Metering
1. Open an audio player or browser tab (e.g. YouTube, Spotify, VLC).
2. Open S_Audio_Pin_Linux.
3. **Expected Result**: The application appears in the "Active Applications" section with its application name and a responsive, animated green/yellow/red audio VU meter tracking the sound in real time.

### Scenario 2: Selective Pinpoint Recording (Master Mix)
1. In S_Audio_Pin_Linux, select 1 application (e.g. Browser) and 1 microphone input.
2. In Settings, select **Format**: `MP3`, **Bitrate**: `320 kbps`, **Mode**: `Single File (Master Mix)`.
3. Click the **Record** button (turns Red, timer starts counting).
4. Speak into the microphone while audio is playing in the selected application.
5. Click **Stop Recording**.
6. **Expected Result**: A single clean `.mp3` file is generated containing both the browser audio and microphone voice mixed cleanly. Unselected apps (e.g. game or background notifications) are completely absent from the recording.

### Scenario 3: Multitrack Stems Recording
1. Select 2 applications and 1 microphone.
2. In Settings, select **Mode**: `Separate Files (Individual Stems)` and **Format**: `WAV`.
3. Click **Record**, wait 10 seconds, then click **Stop**.
4. **Expected Result**: A session folder is created containing 3 separate, perfectly time-synchronized `.wav` files (one per app and one for the microphone).

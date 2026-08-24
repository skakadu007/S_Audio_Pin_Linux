# Data Model: S_Audio_Pin_Linux

**Feature**: Linux Application Audio Monitor & Multi-Source Pinpoint Recorder (`001-audio-pin-recorder`)
**Date**: 2026-08-24
**Status**: Ready

## Entities & Schemas

### 1. `AudioSource`
Represents an active audio-producing application stream or hardware microphone device.

| Field | Type | Description |
|---|---|---|
| `id` | `str` | Unique source identifier (e.g. `sink_input:1519` or `source:1807`) |
| `type` | `enum ("app", "mic")` | Source classification |
| `index` | `int` | PulseAudio/PipeWire sink-input or source index number |
| `name` | `str` | Display name (e.g., "ViberPC", "Firefox", "Built-in Audio Analog Stereo") |
| `process_name` | `Optional[str]` | Binary name (e.g., `firefox`, `viber`, `spotify`) |
| `pid` | `Optional[int]` | Operating system process ID |
| `icon_name` | `Optional[str]` | Desktop theme icon identifier if available |
| `channels` | `int` | Number of audio channels (1 for mono, 2 for stereo) |
| `sample_rate` | `int` | Sample rate in Hz (e.g., 44100, 48000) |
| `volume` | `float` | Current playback/input volume scalar (0.0 - 1.5) |
| `is_muted` | `bool` | Whether the stream/device is currently muted |
| `peak_level` | `float` | Real-time instantaneous peak audio amplitude (0.0 to 1.0) |
| `is_selected` | `bool` | Whether marked for recording by user |

### 2. `RecordingConfig`
Represents user recording settings and preferences.

| Field | Type | Default | Description |
|---|---|---|---|
| `format` | `enum ("wav", "mp3")` | `"mp3"` | Output audio encoding container format |
| `bitrate` | `enum ("128k", "192k", "256k", "320k")` | `"320k"` | Compression bitrate for MP3 |
| `sample_rate` | `int` | `48000` | Target sample rate (44100 / 48000 Hz) |
| `mode` | `enum ("single_mix", "multi_stem")` | `"single_mix"` | `single_mix` (master stereo mix) or `multi_stem` (individual files per source) |
| `output_dir` | `str` | `~/Recordings/S_Audio_Pin` | Target folder for saved recordings |
| `filename_prefix` | `str` | `"rec"` | Prefix for generated recording files |

### 3. `RecordingSession`
Represents an ongoing or completed recording instance.

| Field | Type | Description |
|---|---|---|
| `session_id` | `str` | Unique session UUID / timestamp string |
| `status` | `enum ("idle", "recording", "finalizing", "completed", "error")` | Current session state |
| `start_time` | `Optional[float]` | Epoch timestamp when recording started |
| `duration_secs` | `float` | Elapsed recording duration |
| `config` | `RecordingConfig` | Configuration used for this session |
| `sources` | `List[AudioSource]` | Audio sources included in this session |
| `output_files` | `List[str]` | List of generated file paths |
| `total_bytes` | `int` | Total written file size in bytes |
| `error_message` | `Optional[str]` | Error details if session failed |

---

## State Transitions: Recording Session

```text
[ IDLE ]
   │
   ▼ User selects sources & clicks "Record"
[ RECORDING ] (spawns parec + ffmpeg capture pipelines, updates duration & levels)
   │
   ▼ User clicks "Stop" OR critical system event
[ FINALIZING ] (flushes encoders, closes file descriptors, validates file headers)
   │
   ▼ Success
[ COMPLETED ] (notifies UI, provides file link & play actions)
```

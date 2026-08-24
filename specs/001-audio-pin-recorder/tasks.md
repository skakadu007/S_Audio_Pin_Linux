# Tasks: Linux Application Audio Monitor & Multi-Source Recorder (S_Audio_Pin_Linux)

**Branch**: `001-audio-pin-recorder`
**Feature Directory**: `specs/001-audio-pin-recorder`
**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, dependency management, and directory skeleton

- [x] T001 Create project directories (`src/audio`, `src/config`, `src/server`, `src/ui/css`, `src/ui/js`, `tests/unit`, `tests/integration`)
- [x] T002 Initialize project dependencies (`pulsectl`, `psutil`, `fastapi`, `uvicorn`, `websockets`, `pytest`) in `pyproject.toml`
- [x] T003 [P] Configure pytest test runner in `tests/conftest.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core data structures, configuration persistence, and server foundation

**⚠️ CRITICAL**: Must complete before user story implementation begins

- [x] T004 Implement data models (`AudioSource`, `RecordingConfig`, `RecordingSession`) in `src/models/audio.py`
- [x] T005 [P] Implement persistent configuration manager in `src/config/settings.py`
- [x] T006 [P] Implement Linux desktop process & desktop icon resolver in `src/audio/process_info.py`
- [x] T007 Setup FastAPI application and WebSocket router foundation in `src/server/app.py` and `src/server/ws.py`

**Checkpoint**: Foundation ready — user story implementation can proceed.

---

## Phase 3: User Story 1 - Live Process Audio Monitoring & Visual Metering (Priority: P1) 🎯 MVP

**Goal**: Discover running applications emitting sound and connected microphones, displaying live VU/peak audio level meters.

**Independent Test**: Play audio in any application (browser/player) and verify that S_Audio_Pin_Linux lists the process with a real-time reactive volume level meter.

### Tests for User Story 1
- [x] T008 [P] [US1] Unit test for audio source discovery and peak calculation in `tests/unit/test_monitor.py`

### Implementation for User Story 1
- [x] T009 [US1] Implement PulseAudio / PipeWire sink-input & source scanner in `src/audio/monitor.py`
- [x] T010 [US1] Implement low-overhead real-time peak meter detector loop (30-60 Hz) in `src/audio/monitor.py`
- [x] T011 [US1] Connect monitor service to REST endpoint `/api/sources` and WebSocket `/ws` in `src/server/app.py`
- [x] T012 [P] [US1] Build responsive UI layout, dark theme, and source list cards in `src/ui/index.html` and `src/ui/css/style.css`
- [x] T013 [US1] Implement high-performance 60fps Canvas audio VU / peak meter rendering engine in `src/ui/js/visualizer.js` and `src/ui/js/app.js`

**Checkpoint**: User Story 1 is functional — live audio sources and animated VU meters are visible in real time.

---

## Phase 4: User Story 2 - Pinpoint Multi-Source Audio Recording (Priority: P1)

**Goal**: Allow selective checkbox toggling of multiple processes and microphones, and capture audio cleanly with Record/Stop controls.

**Independent Test**: Select specific applications and mic inputs, record audio, and verify that only selected sources are captured.

### Tests for User Story 2
- [x] T014 [P] [US2] Unit test for audio capture pipeline in `tests/unit/test_recorder.py`

### Implementation for User Story 2
- [x] T015 [US2] Implement isolated stream capture workers using `parec --monitor-stream` and `parec -d` in `src/audio/recorder.py`
- [x] T016 [US2] Implement recording session lifecycle (start, active timer, graceful stop, file finalization) in `src/audio/recorder.py`
- [x] T017 [US2] Add `/api/record/start`, `/api/record/stop`, and `/api/record/status` endpoints in `src/server/app.py`
- [x] T018 [US2] Implement UI multi-selection checkboxes, master Record/Stop action button, and live timer in `src/ui/js/app.js`

**Checkpoint**: User Story 2 is functional — selective audio recording works seamlessly.

---

## Phase 5: User Story 3 - Configurable Audio Output Formats & Multitrack Modes (Priority: P2)

**Goal**: Configure output format (WAV, MP3), bitrates (128k-320k), and switch between Master Mix (single file) and Multitrack Stems (separate files).

**Independent Test**: Record in MP3 320k multitrack mode; verify separate time-synchronized MP3 files are generated.

### Tests for User Story 3
- [x] T019 [P] [US3] Unit test for audio encoder command builder in `tests/unit/test_encoder.py`

### Implementation for User Story 3
- [x] T020 [US3] Implement WAV (PCM) and MP3 (libmp3lame) encoding pipelines in `src/audio/encoder.py`
- [x] T021 [US3] Implement Master Mix (`ffmpeg -filter_complex amix`) and Separate Stems multi-worker routing in `src/audio/recorder.py`
- [x] T022 [US3] Implement `/api/config` GET/POST endpoints with validation in `src/server/app.py`
- [x] T023 [US3] Build modern Settings modal (format picker, bitrate selector, mode switch, directory picker) in `src/ui/index.html` and `src/ui/js/app.js`

**Checkpoint**: User Story 3 is functional — recording formats and multitrack modes work as configured.

---

## Phase 6: User Story 4 - Modern, Fluid Desktop UI & Instant File Management (Priority: P3)

**Goal**: Elevate UI aesthetics (glassmorphism, glowing recording states, smooth micro-animations) and provide instant file access.

**Independent Test**: Finish recording and verify notification banner appears with working "Open Folder" button.

### Implementation for User Story 4
- [x] T024 [P] [US4] Implement `/api/open-folder` system action (`xdg-open`) in `src/server/app.py`
- [x] T025 [US4] Polish UI theme with glassmorphic cards, glowing active meters, badges, and smooth transitions in `src/ui/css/style.css`
- [x] T026 [US4] Implement recording completion card with playback preview and "Open Folder" action in `src/ui/js/app.js`
- [x] T027 [US4] Create main desktop application launcher with automatic browser window launch in `src/main.py`

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: End-to-end testing, documentation, and system packaging

- [x] T028 [P] Write comprehensive project documentation in `README.md`
- [x] T029 Run end-to-end quickstart validation per `specs/001-audio-pin-recorder/quickstart.md`
- [x] T030 Execute complete test suite with `pytest`

---

## Dependencies & Execution Order

```text
Phase 1 (Setup) ────────► Phase 2 (Foundational)
                               │
       ┌───────────────────────┴────────────────────────┐
       ▼                                                ▼
Phase 3: US1 (Monitoring & VU Meters) ──► Phase 4: US2 (Selective Recording)
                                                        │
                                                        ▼
                                          Phase 5: US3 (Formats & Stems)
                                                        │
                                                        ▼
                                          Phase 6: US4 (UI Polish & Launcher)
                                                        │
                                                        ▼
                                          Phase 7: Polish & Validation
```

## Summary Metrics
- **Total Tasks**: 30 (30 Completed)
- **Status**: 100% Implemented & Verified

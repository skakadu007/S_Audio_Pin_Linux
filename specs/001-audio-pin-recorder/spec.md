# Feature Specification: Linux Application Audio Monitor & Multi-Source Recorder (S_Audio_Pin_Linux)

**Feature Branch**: `001-audio-pin-recorder`

**Created**: 2026-08-24

**Status**: Ready for Review

**Input**: "Це має бути легкий додаток який показує запущені процеси на пк з лінукс та відображає поруч з процесом індикатор звуку що виходить з цього процесу (додатку). Можна вибрати декілька процесів та окремо вибрати підключені мікрофони і натиснути кнопку запис. Автоматично записується аудіо. Також з налаштувань має бути можливість обрати формат (wav mp3) бітрейт та чи в один файл записувати чи в різні. Сучасний ЮІ цього додатку."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Live Process Audio Monitoring & Visual Metering (Priority: P1)

As a Linux desktop user, I want to see a list of running applications playing audio with live volume level indicators next to each app, so that I can immediately identify which applications are emitting sound and monitor their output levels.

**Why this priority**: Discovering active audio streams and displaying real-time visual peak/VU meters is the fundamental building block for pinpointing and selecting sound sources.

**Independent Test**: Launch multiple audio-playing applications (e.g., browser, media player) and verify that the application lists them in real time with dynamic, animated audio level meters responding to playback volume.

**Acceptance Scenarios**:
1. **Given** one or more applications are producing audio, **When** the user opens the application, **Then** the application displays each active process with its application name, icon/identifier, and a live audio level meter.
2. **Given** an application starts or stops playing audio, **When** the audio stream state changes, **Then** the list and level meters update automatically without requiring manual refresh.
3. **Given** an application is silent or muted, **When** the list is displayed, **Then** its meter remains at zero/idle state while still remaining selectable.

---

### User Story 2 - Pinpoint Multi-Source Audio Recording (Priority: P1)

As a content creator, streamer, or professional user, I want to select specific running applications and hardware microphones, then start recording with a single click, so that only the selected sound sources are captured cleanly.

**Why this priority**: Core value proposition — selective isolation and simultaneous recording of chosen software streams and microphone inputs without capturing unwanted desktop sounds.

**Independent Test**: Select two specific running applications and one microphone input, click "Record", play audio in both apps while speaking into the mic and playing sound in an unselected app; stop recording and verify that only the selected sources are captured in the resulting audio.

**Acceptance Scenarios**:
1. **Given** a list of running audio-producing processes and detected microphone devices, **When** the user toggles the selection for specific processes and microphones, **Then** the UI clearly highlights the armed recording sources.
2. **Given** at least one audio source is selected, **When** the user clicks the "Record" button, **Then** recording begins immediately, displaying elapsed recording time, active signal indicators, and changing the button to "Stop".
3. **Given** recording is in progress, **When** the user clicks "Stop", **Then** the recording finalizes promptly, writes complete audio files to disk, and presents a notification with quick access to the saved file(s).

---

### User Story 3 - Configurable Audio Output Formats & Multitrack Modes (Priority: P2)

As an audio producer or podcaster, I want to customize recording format (WAV, MP3), audio bitrates, and choose between a single combined mix or separate stems (tracks per source), so that the output fits my editing and archiving workflow.

**Why this priority**: Flexibility in audio format and stem separation is critical for users needing either quick sharing (single MP3 mix) or professional post-production (multitrack WAV stems).

**Independent Test**: In settings, configure output format to MP3 320 kbps with "Separate Stems" mode; record two processes and one microphone for 10 seconds; verify that three individual, time-synchronized MP3 files at 320 kbps are created in a timestamped folder.

**Acceptance Scenarios**:
1. **Given** the settings panel is open, **When** the user selects WAV or MP3 format, **Then** the corresponding format and bitrate options (e.g., 128k, 192k, 256k, 320k for MP3; 16-bit/24-bit PCM for WAV) are available and persisted.
2. **Given** "Single File (Master Mix)" mode is active, **When** recording completes, **Then** all selected process and microphone audio streams are mixed into one single audio file.
3. **Given** "Separate Files (Individual Stems)" mode is active, **When** recording completes, **Then** each selected process and microphone is saved as an individual synchronized audio file in a dedicated session folder.
4. **Given** the user selects a custom output folder, **When** recordings are saved, **Then** files are written to that folder with descriptive names (timestamp, app name/mic name).

---

### User Story 4 - Modern, Fluid Desktop UI & Instant File Management (Priority: P3)

As a user, I want an intuitive, aesthetically pleasing, and responsive modern user interface with dark mode, smooth animations, and instant access to completed recordings.

**Why this priority**: A high-quality, professional user experience elevates usability, reduces cognitive load, and provides immediate visual feedback.

**Independent Test**: Inspect the UI during idle and active recording states to ensure smooth 60fps animations, accessible controls, responsive layout, and one-click "Open Containing Folder" button after recording finishes.

**Acceptance Scenarios**:
1. **Given** the application is running, **When** viewed on high-DPI or standard Linux desktop displays, **Then** typography, contrast, icons, and level meters appear crisp, modern, and aligned.
2. **Given** a recording has just finished, **When** the completion banner appears, **Then** the user can click "Open Folder" or "Play" to access the file immediately.

---

### Edge Cases

- **Process Terminated Mid-Recording**: If an application closes or crashes while being recorded, the recording engine MUST continue recording the remaining active sources without failing or corrupting the output file.
- **Microphone Disconnected Mid-Recording**: If a USB microphone is unplugged during recording, the engine MUST gracefully close that track or insert silence/warning without crashing the app.
- **Zero Sound Emitted**: If a selected process emits complete silence during the recording, the output track/mix MUST maintain accurate timeline synchronization without skipping time.
- **Disk Space Exhaustion**: The application MUST monitor available disk space and alert the user or safely finalize the recording before running out of storage.
- **Simultaneous Multiple Outputs from One App**: Applications with multiple internal audio streams (e.g., browser tabs) MUST be cleanly grouped under the application's process name or clearly distinguished.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST scan and monitor all active Linux desktop audio playback streams (sink inputs) and hardware audio input devices (microphones/sources).
- **FR-002**: System MUST calculate and display real-time audio volume peak and RMS levels for each detected application and microphone with a smooth visual update rate.
- **FR-003**: System MUST identify applications by process name, application title, and desktop icon where available.
- **FR-004**: System MUST allow users to select multiple arbitrary application streams for recording via checkboxes or toggle controls.
- **FR-005**: System MUST allow users to select one or more hardware audio input sources (microphones) independently from application playback streams.
- **FR-006**: System MUST provide clear "Select All", "Deselect All", and "Active Only" filters for quick source management.
- **FR-007**: System MUST capture audio directly from selected application streams and microphone inputs without requiring global system audio rerouting or manual virtual patch cables.
- **FR-008**: System MUST support recording in uncompressed WAV (16-bit / 24-bit PCM) and compressed MP3 formats.
- **FR-009**: System MUST allow user configuration of MP3 encoding bitrates (at least 128 kbps, 192 kbps, 256 kbps, 320 kbps).
- **FR-010**: System MUST support two output recording modes:
  1. *Combined Mixdown*: All chosen sources mixed into a single stereo master file.
  2. *Multitrack Stems*: Each chosen source saved into its own isolated, time-aligned audio file.
- **FR-011**: System MUST allow the user to select and persist a default destination directory for saved recordings.
- **FR-012**: System MUST name output files systematically with timestamp, session identifier, and source names.
- **FR-013**: System MUST display an active recording dashboard with elapsed timer, current file size estimate, and real-time recording signal meters.
- **FR-014**: System MUST ensure lossless timeline synchronization across all captured streams in multitrack mode.
- **FR-015**: System MUST provide a modern desktop UI with sleek dark styling, responsive layouts, and immediate recording feedback.

### Key Entities

- **AudioSource**: Represents an audio-producing entity (Application Process Stream or Hardware Microphone Input). Contains ID, process name, PID, stream index, source type (`app` or `mic`), volume level, peak level, and `is_selected` state.
- **RecordingSession**: Represents an active or historical recording run. Contains session ID, start timestamp, stop timestamp, output directory, mode (`single_mix` vs `multi_stem`), audio format (`wav` vs `mp3`), bitrate, list of captured `AudioSource` entities, and output file paths.
- **AudioSettings**: Persisted user preferences including default output folder, preferred format (`wav` / `mp3`), default bitrate, default recording mode, and UI refresh preferences.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: System discovers and lists newly started audio-producing applications within 500 milliseconds of audio playback initiation.
- **SC-002**: Audio level meters render at a fluid 30 to 60 FPS with less than 50 milliseconds of visual latency relative to the heard sound.
- **SC-003**: Recording engine captures selected streams with 0% buffer drops or underruns under normal desktop workloads.
- **SC-004**: Multi-track stem recordings maintain time synchronization accuracy within 5 milliseconds across all recorded tracks over a 60-minute continuous recording session.
- **SC-005**: CPU utilization of the background monitoring and metering loop remains below 3% on standard desktop quad-core processors.
- **SC-006**: Users can arm sources and initiate recording in under 2 clicks from the main screen.

## Assumptions

- Target operating system is Linux running modern audio servers (PipeWire with PulseAudio compatibility layer or native PulseAudio).
- Microphone permissions and desktop audio access are available under standard user privileges without requiring root/sudo.
- Audio encoding libraries (e.g. standard system codecs / encoders for WAV and MP3) are available in the runtime environment.
- The UI framework will provide native or hardware-accelerated rendering for smooth level meter visualizations.

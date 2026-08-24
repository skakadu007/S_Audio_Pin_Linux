# API & WebSocket Contract: S_Audio_Pin_Linux

**Protocol**: HTTP REST + Real-Time WebSocket
**Base URL**: `http://127.0.0.1:8765/api`
**WebSocket URL**: `ws://127.0.0.1:8765/ws`

---

## 1. REST Endpoints

### `GET /api/sources`
Returns the list of detected running application audio streams and microphone input devices.

#### Response `200 OK`:
```json
{
  "apps": [
    {
      "id": "sink_input:1519",
      "type": "app",
      "index": 1519,
      "name": "Spotify",
      "process_name": "spotify",
      "pid": 4892,
      "icon_name": "spotify",
      "volume": 1.0,
      "is_muted": false,
      "peak_level": 0.65
    }
  ],
  "mics": [
    {
      "id": "source:1807",
      "type": "mic",
      "index": 1807,
      "name": "Вбудоване аудіо Аналогове стерео",
      "process_name": null,
      "pid": null,
      "icon_name": "audio-input-microphone",
      "volume": 0.85,
      "is_muted": false,
      "peak_level": 0.12
    }
  ]
}
```

---

### `GET /api/config`
Retrieves current recording configuration and preferences.

#### Response `200 OK`:
```json
{
  "format": "mp3",
  "bitrate": "320k",
  "mode": "single_mix",
  "output_dir": "/home/s_linux/Recordings/S_Audio_Pin",
  "sample_rate": 48000
}
```

---

### `POST /api/config`
Updates recording configuration.

#### Request Body:
```json
{
  "format": "mp3",
  "bitrate": "320k",
  "mode": "single_mix",
  "output_dir": "/home/s_linux/Recordings/S_Audio_Pin"
}
```

---

### `POST /api/record/start`
Starts audio recording for the specified sources.

#### Request Body:
```json
{
  "source_ids": ["sink_input:1519", "source:1807"],
  "format": "mp3",
  "bitrate": "320k",
  "mode": "single_mix"
}
```

#### Response `200 OK`:
```json
{
  "session_id": "rec_20260824_121500",
  "status": "recording",
  "started_at": 1756026900.12
}
```

---

### `POST /api/record/stop`
Stops the active recording session and returns created file details.

#### Response `200 OK`:
```json
{
  "session_id": "rec_20260824_121500",
  "status": "completed",
  "duration_secs": 42.5,
  "output_files": [
    "/home/s_linux/Recordings/S_Audio_Pin/rec_20260824_121500_mix.mp3"
  ],
  "total_bytes": 1704200
}
```

---

### `GET /api/record/status`
Checks the current recording session state.

---

### `POST /api/open-folder`
Opens the recording directory in the user's default Linux file manager (`xdg-open`).

---

## 2. WebSocket Real-Time Stream (`/ws`)

The WebSocket connection broadcasts high-frequency UI updates (30-60 Hz) for audio peak meters, list changes, and session timers.

### Message: Peak Meters & Source Status
```json
{
  "type": "audio_meters",
  "peaks": {
    "sink_input:1519": 0.74,
    "source:1807": 0.22
  },
  "recording": {
    "is_recording": true,
    "duration_secs": 14.8
  }
}
```

### Message: Stream Added / Removed Event
```json
{
  "type": "source_event",
  "event": "sink_input_new",
  "source_id": "sink_input:1820"
}
```

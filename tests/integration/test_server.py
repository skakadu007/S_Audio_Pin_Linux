from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from s_audio_pin.audio.monitor import audio_monitor
from s_audio_pin.audio.recorder import audio_recorder
from s_audio_pin.config.settings import settings_manager
from s_audio_pin.models.audio import RecordingSession
from s_audio_pin.server.app import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_health_endpoint(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert "ok" in data
    assert "dependencies" in data
    assert "pulse_connected" in data


def test_get_sources(client):
    res = client.get("/api/sources")
    assert res.status_code == 200
    data = res.json()
    assert "apps" in data
    assert "mics" in data
    assert isinstance(data["apps"], list)
    assert isinstance(data["mics"], list)


def test_monitor_armed_endpoint(client):
    res = client.post("/api/monitor/armed", json={"source_ids": ["source:10", "app:proc_spotify"]})
    assert res.status_code == 200
    assert res.json() == {"ok": True}
    assert "source:10" in audio_monitor._monitored_mic_ids


def test_get_and_update_config_and_validation(client):
    res = client.get("/api/config")
    assert res.status_code == 200
    cfg = res.json()
    assert cfg["format"] == "mp3"

    update_res = client.post("/api/config", json={"format": "flac", "mode": "multi_stem", "sample_rate": 44100})
    assert update_res.status_code == 200
    new_cfg = update_res.json()
    assert new_cfg["format"] == "flac"
    assert new_cfg["mode"] == "multi_stem"
    assert new_cfg["sample_rate"] == 44100

    # Invalid literal values rejected with 422
    bad_fmt = client.post("/api/config", json={"format": "aac"})
    assert bad_fmt.status_code == 422
    bad_rate = client.post("/api/config", json={"sample_rate": 12345})
    assert bad_rate.status_code == 422


def test_get_record_status_idle(client):
    res = client.get("/api/record/status")
    assert res.status_code == 200
    status = res.json()
    assert status["is_recording"] is False
    assert "reconnections" in status


def test_record_start_validation_no_sources(client):
    res = client.post("/api/record/start", json={"source_ids": []})
    assert res.status_code == 400


def test_record_start_does_not_mutate_saved_config(client):
    captured = {}

    def fake_start(source_ids, config=None):
        captured["config"] = config
        return True, RecordingSession(session_id="rec_test", status="recording", config=config), ""

    with patch.object(audio_recorder, "start_recording", side_effect=fake_start):
        res = client.post(
            "/api/record/start",
            json={"source_ids": ["app:proc_test"], "format": "ogg", "mode": "multi_stem"},
        )
    assert res.status_code == 200
    assert captured["config"].format == "ogg"
    assert captured["config"].mode == "multi_stem"
    # Persisted config must remain untouched
    assert settings_manager.config.format == "mp3"
    assert settings_manager.config.mode == "single_mix"


def test_open_folder_rejects_outside_output_dir(client):
    res = client.post("/api/open-folder", json={"path": "/etc"})
    assert res.status_code == 400


def test_recordings_list_and_delete_traversal_protection(client):
    out_dir = Path(settings_manager.config.output_dir)
    rec_file = out_dir / "rec_sample.wav"
    rec_file.write_bytes(b"RIFFdata")

    list_res = client.get("/api/recordings")
    assert list_res.status_code == 200
    names = [r["name"] for r in list_res.json()["recordings"]]
    assert "rec_sample.wav" in names

    # Traversal / hidden names rejected
    assert client.delete("/api/recordings/..").status_code in (400, 404)
    assert client.delete("/api/recordings/.hidden").status_code == 400
    assert client.delete("/api/recordings/sub%2Ffile").status_code == 400

    del_res = client.delete("/api/recordings/rec_sample.wav")
    assert del_res.status_code == 200
    assert not rec_file.exists()


def test_api_token_and_origin_enforcement(client):
    app.state.api_token = "secret123"

    # API without token rejected
    assert client.get("/api/config").status_code == 403

    # API with valid token succeeds
    ok_res = client.get("/api/config", headers={"X-API-Token": "secret123"})
    assert ok_res.status_code == 200

    # Bad origin rejected
    bad_origin = client.get(
        "/api/config",
        headers={"X-API-Token": "secret123", "Origin": "https://evil.example"},
    )
    assert bad_origin.status_code == 403

    # Root HTML requires token and injects meta tag
    assert client.get("/").status_code == 403
    root_ok = client.get("/?token=secret123")
    assert root_ok.status_code == 200
    assert '<meta name="api-token" content="secret123">' in root_ok.text

    # WebSocket enforces token (clear cookie set by GET /?token=... first)
    client.cookies.clear()
    with pytest.raises(Exception):
        with client.websocket_connect("/ws"):
            pass

    with client.websocket_connect("/ws?token=secret123") as ws:
        ws.send_text("ping")


def test_static_ui_served(client):
    res = client.get("/")
    assert res.status_code == 200
    assert "S_Audio_Pin" in res.text

import pytest
from fastapi.testclient import TestClient
from src.server.app import app
from src.config.settings import settings_manager


@pytest.fixture
def client():
    return TestClient(app)


def test_get_sources(client):
    res = client.get("/api/sources")
    assert res.status_code == 200
    data = res.json()
    assert "apps" in data
    assert "mics" in data
    assert isinstance(data["apps"], list)
    assert isinstance(data["mics"], list)


def test_get_and_update_config(client):
    res = client.get("/api/config")
    assert res.status_code == 200
    cfg = res.json()
    assert "format" in cfg
    assert "bitrate" in cfg
    assert "mode" in cfg

    # Update config
    update_res = client.post("/api/config", json={"format": "wav", "mode": "multi_stem"})
    assert update_res.status_code == 200
    new_cfg = update_res.json()
    assert new_cfg["format"] == "wav"
    assert new_cfg["mode"] == "multi_stem"


def test_get_record_status_idle(client):
    res = client.get("/api/record/status")
    assert res.status_code == 200
    status = res.json()
    assert "status" in status
    assert status["is_recording"] is False


def test_record_start_validation_no_sources(client):
    res = client.post("/api/record/start", json={"source_ids": []})
    assert res.status_code == 400


def test_static_ui_served(client):
    res = client.get("/")
    assert res.status_code == 200
    assert "S_Audio_Pin" in res.text

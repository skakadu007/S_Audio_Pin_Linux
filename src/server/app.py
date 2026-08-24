import asyncio
import os
import logging
import subprocess
from contextlib import asynccontextmanager
from pathlib import Path
from typing import List, Optional, Dict, Any

logger = logging.getLogger("s_audio_pin.server")

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from ..models.audio import RecordingConfig
from ..config.settings import settings_manager
from ..audio.monitor import audio_monitor
from ..audio.recorder import audio_recorder
from .ws import ws_manager

UI_DIR = Path(__file__).parent.parent / "ui"


# Request / Response Models
class ConfigUpdateRequest(BaseModel):
    format: Optional[str] = None
    bitrate: Optional[str] = None
    sample_rate: Optional[int] = None
    mode: Optional[str] = None
    output_dir: Optional[str] = None


class RecordStartRequest(BaseModel):
    source_ids: List[str]
    format: Optional[str] = None
    bitrate: Optional[str] = None
    mode: Optional[str] = None


class OpenFolderRequest(BaseModel):
    path: Optional[str] = None


# Background loop for WebSocket broadcasting
async def _ws_broadcast_loop():
    while True:
        try:
            if ws_manager.active_connections:
                peaks = audio_monitor.get_peaks()
                rec_status = audio_recorder.get_status()
                payload = {
                    "type": "audio_meters",
                    "peaks": peaks,
                    "recording": {
                        "is_recording": rec_status["is_recording"],
                        "duration_secs": rec_status["duration_secs"],
                        "status": rec_status["status"],
                    },
                }
                await ws_manager.broadcast_json(payload)
            await asyncio.sleep(0.033)  # ~30 Hz smooth updates
        except asyncio.CancelledError:
            break
        except Exception:
            await asyncio.sleep(0.1)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    audio_monitor.start()
    broadcast_task = asyncio.create_task(_ws_broadcast_loop())
    yield
    # Shutdown
    broadcast_task.cancel()
    if audio_recorder.is_recording:
        audio_recorder.stop_recording()
    audio_monitor.stop()


app = FastAPI(title="S_Audio_Pin_Linux API", version="1.0.0", lifespan=lifespan)


# REST Endpoints
@app.get("/api/sources")
def get_sources():
    """Returns detected running audio processes and connected microphones."""
    return audio_monitor.get_sources()


@app.get("/api/config")
def get_config():
    """Returns persisted user settings and preferences."""
    return settings_manager.config.to_dict()


@app.post("/api/config")
def update_config(req: ConfigUpdateRequest):
    """Updates and saves user recording configuration."""
    cfg = settings_manager.config
    data = req.model_dump(exclude_unset=True)
    if not data:
        return cfg.to_dict()

    for k, v in data.items():
        if v is not None and hasattr(cfg, k):
            setattr(cfg, k, v)

    settings_manager.save(cfg)
    return cfg.to_dict()


@app.get("/api/record/status")
def get_record_status():
    """Returns current recording status, active session, and duration."""
    return audio_recorder.get_status()


@app.post("/api/record/start")
def start_recording(req: RecordStartRequest):
    """Starts selective recording of specified application and microphone streams."""
    cfg = settings_manager.config
    # Apply one-off overrides if passed
    if req.format:
        cfg.format = req.format
    if req.bitrate:
        cfg.bitrate = req.bitrate
    if req.mode:
        cfg.mode = req.mode

    success, session, err = audio_recorder.start_recording(req.source_ids, config=cfg)
    if not success or not session:
        raise HTTPException(status_code=400, detail=err or "Failed to start recording")

    return {
        "success": True,
        "session_id": session.session_id,
        "status": session.status,
        "mode": session.config.mode,
        "output_files": session.output_files,
    }


@app.post("/api/record/stop")
def stop_recording():
    """Stops the active recording session and finalizes output files."""
    success, session, err = audio_recorder.stop_recording()
    if not success or not session:
        raise HTTPException(status_code=400, detail=err or "Failed to stop recording")

    return {
        "success": True,
        "session_id": session.session_id,
        "status": session.status,
        "duration_secs": round(session.duration_secs, 1),
        "output_files": session.output_files,
        "total_bytes": session.total_bytes,
    }


@app.post("/api/shutdown")
def shutdown_server():
    """Stops active recording, cleans up audio monitor, closes app window, and shuts down the background server."""
    logger.info("Shutdown requested via API. Finalizing and exiting...")
    try:
        if audio_recorder.is_recording:
            audio_recorder.stop_recording()
    except Exception as e:
        logger.error(f"Error stopping recording on shutdown: {e}")

    try:
        audio_monitor.stop()
    except Exception as e:
        logger.error(f"Error stopping audio monitor on shutdown: {e}")

    # Terminate standalone Chrome app window
    try:
        subprocess.run(["pkill", "-f", "app_profile"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        logger.debug(f"Error terminating app window: {e}")

    def _delayed_exit():
        import time, os
        time.sleep(0.15)
        os._exit(0)

    import threading
    threading.Thread(target=_delayed_exit, daemon=True).start()
    return {"success": True, "message": "Server shutting down..."}


@app.post("/api/open-folder")
def open_folder(req: Optional[OpenFolderRequest] = None):
    """Opens the recordings directory in the Linux desktop file manager."""
    target_path = req.path if req and req.path else settings_manager.config.output_dir
    p = Path(target_path).expanduser().resolve()
    p.mkdir(parents=True, exist_ok=True)

    try:
        subprocess.Popen(["xdg-open", str(p)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return {"success": True, "path": str(p)}
    except Exception as e:
        try:
            subprocess.Popen(["gio", "open", str(p)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return {"success": True, "path": str(p)}
        except Exception as e2:
            raise HTTPException(status_code=500, detail=f"Failed to open directory: {e2}")


@app.get("/api/recordings")
def list_recordings():
    """Lists recent recording files and folders."""
    output_dir = Path(settings_manager.config.output_dir).expanduser().resolve()
    if not output_dir.exists():
        return {"recordings": []}

    items = []
    try:
        for entry in sorted(output_dir.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
            if entry.name.startswith("."):
                continue
            stat = entry.stat()
            items.append({
                "name": entry.name,
                "path": str(entry),
                "is_dir": entry.is_dir(),
                "size_bytes": stat.st_size if entry.is_file() else 0,
                "modified": stat.st_mtime,
            })
    except Exception as e:
        logger.error(f"Error listing recordings: {e}")

    return {"recordings": items[:25]}


# WebSocket Endpoint for 30-60Hz UI Meters
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep connection open & handle incoming pings/messages
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket)
    except Exception:
        await ws_manager.disconnect(websocket)


# Mount Static UI Files
if UI_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(UI_DIR)), name="static")

    @app.get("/")
    def serve_index():
        return FileResponse(str(UI_DIR / "index.html"))

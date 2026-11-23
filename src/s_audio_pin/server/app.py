import asyncio
import html
import logging
import secrets
import shutil
import subprocess
import threading
from contextlib import asynccontextmanager
from pathlib import Path
from typing import List, Literal, Optional
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from ..audio.monitor import audio_monitor
from ..audio.recorder import audio_recorder, check_audio_dependencies
from ..config.settings import settings_manager
from ..models.audio import AudioBitrate, AudioFormat, RecordingMode
from ..window import pick_folder_dialog
from .ws import ws_manager

logger = logging.getLogger("s_audio_pin.server")

UI_DIR = Path(__file__).resolve().parent.parent / "ui"
TOKEN_COOKIE_NAME = "s_audio_pin_token"


# Request Models
class ConfigUpdateRequest(BaseModel):
    format: Optional[AudioFormat] = None
    bitrate: Optional[AudioBitrate] = None
    sample_rate: Optional[Literal[44100, 48000]] = None
    mode: Optional[RecordingMode] = None
    output_dir: Optional[str] = None


class RecordStartRequest(BaseModel):
    source_ids: List[str]
    format: Optional[AudioFormat] = None
    bitrate: Optional[AudioBitrate] = None
    sample_rate: Optional[Literal[44100, 48000]] = None
    mode: Optional[RecordingMode] = None


class ArmedSourcesRequest(BaseModel):
    source_ids: List[str]


class OpenFolderRequest(BaseModel):
    path: Optional[str] = None


def _is_valid_token(provided: Optional[str], expected: Optional[str]) -> bool:
    if not expected:
        return True
    if not provided:
        return False
    return secrets.compare_digest(provided, expected)


def _is_origin_allowed(origin: Optional[str], expected_netloc: str) -> bool:
    if not origin:
        return True
    try:
        parsed = urlparse(origin)
        return parsed.scheme in ("http", "https") and parsed.netloc == expected_netloc
    except Exception:
        return False


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
                        "reconnections": rec_status["reconnections"],
                        "warnings": rec_status["warnings"],
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
    audio_monitor.start()
    broadcast_task = asyncio.create_task(_ws_broadcast_loop())
    try:
        yield
    finally:
        broadcast_task.cancel()
        try:
            await broadcast_task
        except asyncio.CancelledError:
            pass
        if audio_recorder.is_recording:
            audio_recorder.stop_recording()
        audio_monitor.stop()


app = FastAPI(title="S_Audio_Pin_Linux API", version="0.2.1", lifespan=lifespan)
app.state.api_token = None
app.state.shutdown_callback = None


@app.middleware("http")
async def security_middleware(request: Request, call_next):
    origin = request.headers.get("origin")
    if origin and not _is_origin_allowed(origin, request.url.netloc):
        return JSONResponse({"detail": "Invalid Origin"}, status_code=403)

    expected_token: Optional[str] = getattr(app.state, "api_token", None)
    if expected_token and request.url.path.startswith("/api/"):
        header_token = request.headers.get("x-api-token")
        cookie_token = request.cookies.get(TOKEN_COOKIE_NAME)
        if not (
            _is_valid_token(header_token, expected_token)
            or _is_valid_token(cookie_token, expected_token)
        ):
            return JSONResponse({"detail": "Forbidden"}, status_code=403)

    return await call_next(request)


# REST Endpoints
@app.get("/api/health")
def get_health():
    """Returns system dependency readiness and PipeWire/PulseAudio connection status."""
    deps = check_audio_dependencies()
    return {
        "ok": bool(deps["ready"]),
        "dependencies": deps,
        "pulse_connected": audio_monitor.pulse_connected,
    }


@app.get("/api/sources")
def get_sources():
    """Returns detected running audio processes and connected microphones."""
    return audio_monitor.get_sources()


@app.post("/api/monitor/armed")
def set_armed_sources(req: ArmedSourcesRequest):
    """Notifies AudioMonitor which sources are armed so only armed wired mics run VU meters."""
    audio_monitor.set_monitored_mics(req.source_ids)
    return {"ok": True}


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

    if "output_dir" in data:
        raw_out = (data["output_dir"] or "").strip()
        if not raw_out:
            raise HTTPException(status_code=400, detail="Папка збереження не може бути порожньою")
        data["output_dir"] = raw_out

    prev_cfg = cfg.clone()
    new_cfg = cfg.clone(**data)
    if not settings_manager.save(new_cfg):
        settings_manager._config = prev_cfg
        raise HTTPException(
            status_code=400,
            detail=f"Не вдалося зберегти налаштування або створити папку: {new_cfg.output_dir}",
        )
    return new_cfg.to_dict()


@app.get("/api/record/status")
def get_record_status():
    """Returns current recording status, active session, and duration."""
    return audio_recorder.get_status()


@app.post("/api/record/start")
def start_recording(req: RecordStartRequest):
    """Starts selective recording of specified application and microphone streams."""
    cfg = settings_manager.config.clone(
        format=req.format,
        bitrate=req.bitrate,
        sample_rate=req.sample_rate,
        mode=req.mode,
    )

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
        "reconnections": session.reconnections,
        "warnings": list(session.warnings),
    }


@app.post("/api/pick-folder")
def pick_folder():
    """Opens a native directory chooser dialog and returns the selected path."""
    chosen = pick_folder_dialog(initial_dir=settings_manager.config.output_dir)
    return {
        "selected": bool(chosen),
        "path": chosen,
    }


@app.post("/api/shutdown")
def shutdown_server():
    """Stops active recording, cleans up audio monitor, and triggers graceful application shutdown."""
    logger.info("Shutdown requested via API. Finalizing and exiting...")
    try:
        if audio_recorder.is_recording:
            audio_recorder.stop_recording()
    except Exception as e:
        logger.error("Error stopping recording on shutdown: %s", e)

    try:
        audio_monitor.stop()
    except Exception as e:
        logger.error("Error stopping audio monitor on shutdown: %s", e)

    cb = getattr(app.state, "shutdown_callback", None)
    if callable(cb):
        timer = threading.Timer(0.1, cb)
        timer.daemon = True
        timer.start()

    return {"success": True, "message": "Server shutting down..."}


@app.post("/api/open-folder")
def open_folder(req: Optional[OpenFolderRequest] = None):
    """Opens the recordings directory (or a safe subfolder inside it) in the file manager."""
    base_dir = Path(settings_manager.config.output_dir).expanduser().resolve()

    if req and req.path:
        candidate = Path(req.path).expanduser().resolve()
        if candidate != base_dir and not candidate.is_relative_to(base_dir):
            raise HTTPException(
                status_code=400,
                detail="Дозволено відкривати лише папку записів або її підпапки",
            )
        if not candidate.exists():
            raise HTTPException(status_code=404, detail="Папку не знайдено")
        target = candidate.parent if candidate.is_file() else candidate
    else:
        base_dir.mkdir(parents=True, exist_ok=True)
        target = base_dir

    for opener in (["xdg-open", str(target)], ["gio", "open", str(target)]):
        try:
            subprocess.Popen(opener, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return {"success": True, "path": str(target)}
        except FileNotFoundError:
            continue
        except Exception as e:
            logger.debug("Folder opener %s failed: %s", opener[0], e)

    raise HTTPException(status_code=500, detail="Не вдалося відкрити папку у файловому менеджері")


@app.get("/api/recordings")
def list_recordings():
    """Lists recent recording files and stem folders."""
    output_dir = Path(settings_manager.config.output_dir).expanduser().resolve()
    if not output_dir.exists():
        return {"recordings": []}

    items = []
    try:
        for entry in sorted(output_dir.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
            if entry.name.startswith("."):
                continue
            stat = entry.stat()
            if entry.is_dir():
                size_bytes = sum(
                    f.stat().st_size for f in entry.rglob("*") if f.is_file()
                )
            else:
                size_bytes = stat.st_size
            items.append({
                "name": entry.name,
                "path": str(entry),
                "is_dir": entry.is_dir(),
                "size_bytes": size_bytes,
                "modified": stat.st_mtime,
            })
    except Exception as e:
        logger.error("Error listing recordings: %s", e)

    return {"recordings": items[:50]}


@app.delete("/api/recordings/{name:path}")
def delete_recording(name: str):
    """Deletes a recording file or stem directory strictly inside output_dir."""
    if not name or name in (".", "..") or "/" in name or "\\" in name or name.startswith("."):
        raise HTTPException(status_code=400, detail="Некоректна назва запису")

    base_dir = Path(settings_manager.config.output_dir).expanduser().resolve()
    target = (base_dir / name).resolve()

    if target.parent != base_dir or target == base_dir:
        raise HTTPException(status_code=400, detail="Заборонений шлях видалення")

    if not target.exists():
        raise HTTPException(status_code=404, detail="Запис не знайдено")

    try:
        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink()
    except OSError as e:
        raise HTTPException(status_code=500, detail=f"Не вдалося видалити запис: {e}")

    return {"success": True, "deleted": name}


# WebSocket Endpoint for 30Hz UI Meters
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    origin = websocket.headers.get("origin")
    if origin and not _is_origin_allowed(origin, websocket.url.netloc):
        await websocket.close(code=4403)
        return

    expected_token: Optional[str] = getattr(app.state, "api_token", None)
    if expected_token:
        query_token = websocket.query_params.get("token")
        cookie_token = websocket.cookies.get(TOKEN_COOKIE_NAME)
        if not (
            _is_valid_token(query_token, expected_token)
            or _is_valid_token(cookie_token, expected_token)
        ):
            await websocket.close(code=4403)
            return

    await ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket)
    except Exception:
        await ws_manager.disconnect(websocket)


# Mount Static UI Files
if UI_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(UI_DIR)), name="static")

    @app.get("/")
    def serve_index(request: Request, token: Optional[str] = None):
        expected_token: Optional[str] = getattr(app.state, "api_token", None)
        index_path = UI_DIR / "index.html"
        if not expected_token:
            return FileResponse(str(index_path))

        cookie_token = request.cookies.get(TOKEN_COOKIE_NAME)
        if not (
            _is_valid_token(token, expected_token)
            or _is_valid_token(cookie_token, expected_token)
        ):
            raise HTTPException(status_code=403, detail="Forbidden")

        content = index_path.read_text(encoding="utf-8")
        meta_tag = f'  <meta name="api-token" content="{html.escape(expected_token, quote=True)}">\n'
        if "</head>" in content:
            content = content.replace("</head>", f"{meta_tag}</head>", 1)
        else:
            content = meta_tag + content

        response = HTMLResponse(content)
        response.set_cookie(
            key=TOKEN_COOKIE_NAME,
            value=expected_token,
            httponly=True,
            samesite="strict",
            path="/",
        )
        return response

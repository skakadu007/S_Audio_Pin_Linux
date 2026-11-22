import asyncio
import json
from typing import Set, Dict, Any
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        async with self._lock:
            self.active_connections.add(websocket)

    async def disconnect(self, websocket: WebSocket):
        async with self._lock:
            self.active_connections.discard(websocket)

    async def broadcast_json(self, data: Dict[str, Any]):
        if not self.active_connections:
            return

        dead_connections = []
        payload = json.dumps(data)
        async with self._lock:
            for connection in list(self.active_connections):
                try:
                    await connection.send_text(payload)
                except Exception:
                    dead_connections.append(connection)

            for dead in dead_connections:
                self.active_connections.discard(dead)


# Global WebSocket connection manager
ws_manager = ConnectionManager()

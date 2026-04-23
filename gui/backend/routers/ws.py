import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from core.resources import get_resources
from core.ports import get_open_ports

router = APIRouter()


@router.websocket("/ws/resources")
async def ws_resources(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = get_resources()
            await websocket.send_text(json.dumps(data))
            await asyncio.sleep(5)
    except (WebSocketDisconnect, Exception):
        pass


@router.websocket("/ws/ports")
async def ws_ports(websocket: WebSocket):
    await websocket.accept()
    prev: set[int] = set()
    try:
        while True:
            ports = get_open_ports()
            current = {p["port"] for p in ports}
            opened = current - prev
            closed = prev - current
            if prev:
                changes = [
                    {"port": p, "event": "opened"} for p in sorted(opened)
                ] + [
                    {"port": p, "event": "closed"} for p in sorted(closed)
                ]
                if changes:
                    await websocket.send_text(json.dumps({"changes": changes, "ports": ports}))
            else:
                await websocket.send_text(json.dumps({"changes": [], "ports": ports}))
            prev = current
            await asyncio.sleep(5)
    except (WebSocketDisconnect, Exception):
        pass

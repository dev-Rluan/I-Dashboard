import json
import os
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request

router = APIRouter()

_AGENT_TOKEN = os.getenv("AGENT_TOKEN", "")


def _verify(request: Request) -> None:
    if not _AGENT_TOKEN:
        return
    if request.headers.get("X-Agent-Token", "") != _AGENT_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid agent token")


@router.post("/report")
async def report(request: Request, payload: dict):
    _verify(request)

    from gui.backend.db import get_db

    agent_id = str(payload.get("agent_id") or payload.get("hostname") or "unknown")
    now = datetime.now(timezone.utc).isoformat()
    ip = request.client.host if request.client else "unknown"

    with get_db() as db:
        db.execute(
            """INSERT INTO agents (id, name, os, ip, last_seen)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(id) DO UPDATE SET
                 name=excluded.name, os=excluded.os,
                 ip=excluded.ip, last_seen=excluded.last_seen""",
            (agent_id, payload.get("hostname", agent_id), payload.get("os", ""), ip, now),
        )
        db.execute(
            "INSERT INTO snapshots (agent_id, timestamp, data) VALUES (?, ?, ?)",
            (agent_id, now, json.dumps(payload)),
        )

    return {"ok": True}


@router.get("")
def list_agents():
    from gui.backend.db import get_db

    with get_db() as db:
        rows = db.execute(
            "SELECT id, name, os, ip, last_seen FROM agents ORDER BY last_seen DESC"
        ).fetchall()
    return [dict(r) for r in rows]


@router.get("/{agent_id}/latest")
def get_latest(agent_id: str):
    from gui.backend.db import get_db

    with get_db() as db:
        row = db.execute(
            "SELECT data, timestamp FROM snapshots WHERE agent_id=? ORDER BY timestamp DESC LIMIT 1",
            (agent_id,),
        ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="에이전트를 찾을 수 없습니다")

    data = json.loads(row["data"])
    data["_timestamp"] = row["timestamp"]
    return data


@router.get("/{agent_id}/history")
def get_history(agent_id: str, limit: int = 60):
    from gui.backend.db import get_db

    with get_db() as db:
        rows = db.execute(
            """SELECT timestamp, data FROM snapshots
               WHERE agent_id=? ORDER BY timestamp DESC LIMIT ?""",
            (agent_id, min(limit, 1000)),
        ).fetchall()

    return [{"timestamp": r["timestamp"], **json.loads(r["data"])} for r in rows]

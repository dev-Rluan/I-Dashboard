import json
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

_DB_PATH = os.getenv("DB_PATH", "data/dashboard.db")


def _connect() -> sqlite3.Connection:
    Path(_DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(_DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db() -> None:
    conn = _connect()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS agents (
            id        TEXT PRIMARY KEY,
            name      TEXT NOT NULL,
            os        TEXT,
            ip        TEXT,
            last_seen TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS snapshots (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_id  TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            data      TEXT NOT NULL,
            FOREIGN KEY (agent_id) REFERENCES agents(id)
        );

        CREATE INDEX IF NOT EXISTS idx_snap_agent_time
            ON snapshots(agent_id, timestamp DESC);
    """)
    conn.commit()
    conn.close()


@contextmanager
def get_db():
    conn = _connect()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

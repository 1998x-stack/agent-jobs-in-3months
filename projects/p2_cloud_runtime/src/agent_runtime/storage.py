"""SQLite lease-based task queue, with fencing tokens for a teaching MVP."""
import json
import sqlite3
import uuid
from pathlib import Path
from typing import Any

class TaskStore:
    def __init__(self, db_path: str | Path = ":memory:") -> None:
        self.conn = sqlite3.connect(str(db_path), isolation_level=None)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY,
                request_key TEXT UNIQUE NOT NULL,
                payload TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'queued',
                attempt INTEGER NOT NULL DEFAULT 0,
                lease_until REAL,
                claim_token TEXT,
                result TEXT
            )
        """)

    def submit(self, request_key: str, payload: dict[str, Any]) -> int:
        if not request_key:
            raise ValueError("request_key is required")
        self.conn.execute(
            "INSERT OR IGNORE INTO jobs (request_key, payload) VALUES (?, ?)",
            (request_key, json.dumps(payload, sort_keys=True)),
        )
        row = self.conn.execute(
            "SELECT id FROM jobs WHERE request_key = ?", (request_key,)
        ).fetchone()
        return int(row["id"])

    def claim(self, now: float, lease_seconds: float = 30.0) -> dict | None:
        if lease_seconds <= 0:
            raise ValueError("lease must be positive")
        self.conn.execute("BEGIN IMMEDIATE")
        try:
            row = self.conn.execute("""
                SELECT * FROM jobs
                WHERE status = 'queued'
                   OR (status = 'running' AND lease_until <= ?)
                ORDER BY id LIMIT 1
            """, (now,)).fetchone()
            if row is None:
                self.conn.execute("COMMIT")
                return None
            token = uuid.uuid4().hex
            self.conn.execute("""
                UPDATE jobs SET status='running', attempt=attempt+1,
                   lease_until=?, claim_token=? WHERE id=?
            """, (now + lease_seconds, token, row["id"]))
            self.conn.execute("COMMIT")
            return {"id": int(row["id"]), "payload": json.loads(row["payload"]),
                    "token": token, "attempt": int(row["attempt"]) + 1}
        except Exception:
            self.conn.execute("ROLLBACK")
            raise

    def complete(self, job_id: int, token: str, result: str, now: float) -> bool:
        cursor = self.conn.execute("""
            UPDATE jobs SET status='completed', result=?, lease_until=NULL
            WHERE id=? AND claim_token=? AND status='running'
              AND lease_until > ?
        """, (result, job_id, token, now))
        return cursor.rowcount == 1

    def get(self, job_id: int) -> dict | None:
        row = self.conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
        return dict(row) if row is not None else None

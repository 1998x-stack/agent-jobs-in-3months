"""B02/B03: atomic, actor-scoped idempotent run queue in a local SQLite file.

Teaching semantics:
  - A request key is unique within a tenant, and replay with different actor or
    payload is a conflict (409 at the HTTP boundary).
  - Every write and state transition uses BEGIN IMMEDIATE + COMMIT or ROLLBACK.
  - Workers receive a fencing token and an expiring lease; stale completion fails.
  - Workers may execute *read-only* actions more than once after lease expiry.
    Exactly-once EXTERNAL side effects are not guaranteed by SQLite fencing.
No untrusted SQL, credentials, or production financial side effects.
"""
from contextlib import contextmanager
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import time
import uuid
from typing import Iterator

from agent_harness.scoped_memory import MemoryScope


_KEY = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{7,127}$")
MAX_ATTEMPTS = 3


class RunConflict(ValueError):
    """Idempotency key conflict or invalid state transition."""


class RunMissing(LookupError):
    """No run is visible to this actor in their tenant."""


@dataclass(frozen=True)
class RunRecord:
    run_id: str
    tenant_id: str
    user_id: str
    question: str
    max_tasks: int
    max_context_chars: int
    status: str
    attempt: int
    result: dict | None
    error_code: str | None
    created_at: float
    updated_at: float


@dataclass(frozen=True)
class RunClaim:
    run: RunRecord
    claim_token: str
    lease_until: float


class RunRepository:
    """Create one SQLite connection per operation (safe across API threads)."""

    def __init__(self, filename: str | Path) -> None:
        self.filename = str(filename)
        if self.filename == ":memory:":
            raise ValueError("use a filesystem SQLite file for cross-connection operations")
        Path(self.filename).parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("""
                CREATE TABLE IF NOT EXISTS agent_runs (
                    run_id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    request_key TEXT NOT NULL,
                    fingerprint TEXT NOT NULL,
                    question TEXT NOT NULL,
                    max_tasks INTEGER NOT NULL,
                    max_context_chars INTEGER NOT NULL,
                    status TEXT NOT NULL
                      CHECK(status IN ('queued','running','completed','failed')),
                    attempt INTEGER NOT NULL DEFAULT 0,
                    claim_token TEXT,
                    lease_until REAL,
                    result_json TEXT,
                    error_code TEXT,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    UNIQUE(tenant_id, request_key)
                )
            """)
            db.execute("""
                CREATE INDEX IF NOT EXISTS idx_agent_runs_queue
                ON agent_runs(status, created_at)
            """)

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        db = sqlite3.connect(self.filename, isolation_level=None, timeout=10)
        db.row_factory = sqlite3.Row
        try:
            db.execute("PRAGMA busy_timeout=10000")
            db.execute("PRAGMA foreign_keys=ON")
            yield db
        finally:
            db.close()

    @contextmanager
    def _write(self) -> Iterator[sqlite3.Connection]:
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                yield db
                db.execute("COMMIT")
            except BaseException:
                db.execute("ROLLBACK")
                raise

    @staticmethod
    def _run(row: sqlite3.Row) -> RunRecord:
        return RunRecord(
            run_id=row["run_id"],
            tenant_id=row["tenant_id"],
            user_id=row["user_id"],
            question=row["question"],
            max_tasks=int(row["max_tasks"]),
            max_context_chars=int(row["max_context_chars"]),
            status=row["status"],
            attempt=int(row["attempt"]),
            result=json.loads(row["result_json"]) if row["result_json"] is not None else None,
            error_code=row["error_code"],
            created_at=float(row["created_at"]),
            updated_at=float(row["updated_at"]),
        )

    def submit(
        self,
        scope: MemoryScope,
        *,
        idempotency_key: str,
        question: str,
        max_tasks: int = 3,
        max_context_chars: int = 2200,
        now: float | None = None,
    ) -> tuple[RunRecord, bool]:
        if not isinstance(scope, MemoryScope):
            raise TypeError("trusted actor scope required")
        if not isinstance(idempotency_key, str) or not _KEY.fullmatch(idempotency_key):
            raise ValueError("Idempotency-Key must be 8..128 safe characters")
        if not isinstance(question, str) or not question.strip() or len(question) > 600:
            raise ValueError("question must contain 1..600 characters")
        if type(max_tasks) is not int or not 1 <= max_tasks <= 3:
            raise ValueError("max_tasks must be in 1..3")
        if type(max_context_chars) is not int or not 800 <= max_context_chars <= 8000:
            raise ValueError("max_context_chars must be in 800..8000")
        question = question.strip()
        request_body = json.dumps({
            "user_id": scope.user_id,
            "question": question,
            "max_tasks": max_tasks,
            "max_context_chars": max_context_chars,
        }, sort_keys=True, separators=(",", ":"))
        fingerprint = hashlib.sha256(request_body.encode("utf-8")).hexdigest()
        stamp = time.time() if now is None else float(now)
        with self._write() as db:
            found = db.execute("""
                SELECT * FROM agent_runs WHERE tenant_id=? AND request_key=?
            """, (scope.tenant_id, idempotency_key)).fetchone()
            if found is not None:
                if found["fingerprint"] != fingerprint:
                    raise RunConflict("same idempotency key used with a different request")
                return self._run(found), False
            run_id = uuid.uuid4().hex
            db.execute("""
                INSERT INTO agent_runs (
                    run_id,tenant_id,user_id,request_key,fingerprint,question,
                    max_tasks,max_context_chars,status,created_at,updated_at
                ) VALUES (?,?,?,?,?,?,?,?,'queued',?,?)
            """, (
                run_id, scope.tenant_id, scope.user_id, idempotency_key,
                fingerprint, question, max_tasks, max_context_chars, stamp, stamp,
            ))
            row = db.execute(
                "SELECT * FROM agent_runs WHERE run_id=?", (run_id,)
            ).fetchone()
            return self._run(row), True

    def get(self, scope: MemoryScope, run_id: str) -> RunRecord | None:
        if not isinstance(scope, MemoryScope):
            raise TypeError("trusted actor scope required")
        with self._connect() as db:
            row = db.execute("""
                SELECT * FROM agent_runs
                WHERE run_id=? AND tenant_id=? AND user_id=?
            """, (run_id, scope.tenant_id, scope.user_id)).fetchone()
            return self._run(row) if row is not None else None

    def claim_next(
        self, *, now: float | None = None, lease_seconds: float = 120
    ) -> RunClaim | None:
        if type(lease_seconds) not in (int, float) or not 0 < lease_seconds <= 3600:
            raise ValueError("lease_seconds must be in (0,3600]")
        stamp = time.time() if now is None else float(now)
        with self._write() as db:
            row = db.execute("""
                SELECT * FROM agent_runs
                WHERE attempt < ?
                  AND (status='queued' OR
                       (status='running' AND lease_until <= ?))
                ORDER BY created_at, run_id LIMIT 1
            """, (MAX_ATTEMPTS, stamp)).fetchone()
            if row is None:
                return None
            token = uuid.uuid4().hex
            deadline = stamp + lease_seconds
            db.execute("""
                UPDATE agent_runs
                SET status='running', attempt=attempt+1, claim_token=?,
                    lease_until=?, updated_at=?
                WHERE run_id=?
            """, (token, deadline, stamp, row["run_id"]))
            updated = db.execute(
                "SELECT * FROM agent_runs WHERE run_id=?", (row["run_id"],)
            ).fetchone()
            return RunClaim(self._run(updated), token, deadline)

    def complete(
        self,
        claim: RunClaim,
        result: dict,
        *,
        now: float | None = None,
    ) -> bool:
        if not isinstance(result, dict):
            raise ValueError("result must be a structured object")
        encoded = json.dumps(result, ensure_ascii=False, sort_keys=True)
        if len(encoded) > 16_000:
            raise ValueError("result payload exceeds the demo limit")
        stamp = time.time() if now is None else float(now)
        with self._write() as db:
            cursor = db.execute("""
                UPDATE agent_runs
                SET status='completed', result_json=?, error_code=NULL,
                    claim_token=NULL, lease_until=NULL, updated_at=?
                WHERE run_id=? AND status='running'
                  AND claim_token=? AND lease_until>?
            """, (encoded, stamp, claim.run.run_id, claim.claim_token, stamp))
            return cursor.rowcount == 1

    def fail(
        self,
        claim: RunClaim,
        *,
        error_code: str = "worker_failed",
        now: float | None = None,
    ) -> bool:
        if not re.fullmatch(r"[a-z][a-z_]{0,31}", error_code):
            raise ValueError("only generic safe error codes may be recorded")
        stamp = time.time() if now is None else float(now)
        with self._write() as db:
            cursor = db.execute("""
                UPDATE agent_runs SET status='failed', error_code=?,
                    claim_token=NULL, lease_until=NULL, updated_at=?
                WHERE run_id=? AND status='running'
                  AND claim_token=? AND lease_until>?
            """, (error_code, stamp, claim.run.run_id, claim.claim_token, stamp))
            return cursor.rowcount == 1

    def retry(self, scope: MemoryScope, run_id: str, *, now: float | None = None) -> RunRecord:
        if not isinstance(scope, MemoryScope):
            raise TypeError("trusted actor scope required")
        stamp = time.time() if now is None else float(now)
        with self._write() as db:
            row = db.execute("""
                SELECT * FROM agent_runs WHERE run_id=? AND tenant_id=? AND user_id=?
            """, (run_id, scope.tenant_id, scope.user_id)).fetchone()
            if row is None:
                raise RunMissing("run does not exist for actor")
            if row["status"] == "queued":
                return self._run(row)  # duplicate retry is a no-op
            if row["status"] != "failed":
                raise RunConflict("only failed or queued runs can be retried")
            if int(row["attempt"]) >= MAX_ATTEMPTS:
                raise RunConflict("attempt budget exhausted")
            db.execute("""
                UPDATE agent_runs SET status='queued', error_code=NULL,
                    result_json=NULL, claim_token=NULL, lease_until=NULL,
                    updated_at=? WHERE run_id=?
            """, (stamp, run_id))
            row = db.execute("SELECT * FROM agent_runs WHERE run_id=?", (run_id,)).fetchone()
            return self._run(row)

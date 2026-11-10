"""A09: scoped, SQLite-backed memory for a teaching Agent.

Only caller-supplied/approved facts can be persisted. Model outputs and retrieved
text are NEVER automatically written. Scope is bound by the application caller,
not accepted from model tool arguments. No encryption or enterprise identity
provider is provided; store only fictional/nonsensitive data.
"""
from dataclasses import dataclass
from pathlib import Path
import re
import sqlite3
import time


_KEY_RE = re.compile(r"^[a-z][a-z0-9_.-]{0,63}$")
_ALLOWED_SOURCES = {"explicit_user", "operator_approved"}


@dataclass(frozen=True)
class MemoryScope:
    tenant_id: str
    user_id: str

    def __post_init__(self) -> None:
        if not self.tenant_id or not self.tenant_id.strip():
            raise ValueError("tenant_id required")
        if not self.user_id or not self.user_id.strip():
            raise ValueError("user_id required")


@dataclass(frozen=True)
class MemoryFact:
    key: str
    value: str
    source: str
    revision: int
    expires_at: float | None


class ScopedMemoryStore:
    def __init__(self, filename: str | Path = ":memory:") -> None:
        self.conn = sqlite3.connect(str(filename), timeout=5.0)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS memory_facts (
                tenant_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                source TEXT NOT NULL,
                updated_at REAL NOT NULL,
                expires_at REAL,
                revision INTEGER NOT NULL DEFAULT 1,
                PRIMARY KEY (tenant_id, user_id, key)
            )
        """)
        self.conn.commit()

    def __enter__(self) -> "ScopedMemoryStore":
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        self.close()

    def close(self) -> None:
        self.conn.close()

    def put(
        self,
        scope: MemoryScope,
        key: str,
        value: str,
        *,
        source: str,
        ttl_seconds: float | None = None,
        now: float | None = None,
    ) -> int:
        if not isinstance(scope, MemoryScope):
            raise TypeError("trusted application scope required")
        if not isinstance(key, str) or not _KEY_RE.fullmatch(key):
            raise ValueError("invalid memory key")
        if not isinstance(value, str) or not value.strip() or len(value) > 500:
            raise ValueError("memory value must be 1..500 chars")
        if source not in _ALLOWED_SOURCES:
            raise PermissionError("automatic model memory writes are not authorized")
        if ttl_seconds is not None and (
            type(ttl_seconds) not in (int, float) or not 0 < ttl_seconds <= 30 * 86400
        ):
            raise ValueError("invalid TTL")
        timestamp = time.time() if now is None else float(now)
        expiry = timestamp + ttl_seconds if ttl_seconds is not None else None
        with self.conn:
            self.conn.execute("""
                INSERT INTO memory_facts
                    (tenant_id, user_id, key, value, source, updated_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(tenant_id, user_id, key) DO UPDATE SET
                    value=excluded.value,
                    source=excluded.source,
                    updated_at=excluded.updated_at,
                    expires_at=excluded.expires_at,
                    revision=memory_facts.revision+1
            """, (
                scope.tenant_id, scope.user_id, key, value.strip(),
                source, timestamp, expiry,
            ))
        row = self.conn.execute("""
            SELECT revision FROM memory_facts
            WHERE tenant_id=? AND user_id=? AND key=?
        """, (scope.tenant_id, scope.user_id, key)).fetchone()
        return int(row["revision"])

    def get(
        self, scope: MemoryScope, key: str, *, now: float | None = None
    ) -> MemoryFact | None:
        if not isinstance(scope, MemoryScope):
            raise TypeError("trusted application scope required")
        timestamp = time.time() if now is None else float(now)
        row = self.conn.execute("""
            SELECT key, value, source, revision, expires_at FROM memory_facts
            WHERE tenant_id=? AND user_id=? AND key=?
              AND (expires_at IS NULL OR expires_at > ?)
        """, (scope.tenant_id, scope.user_id, key, timestamp)).fetchone()
        return MemoryFact(**dict(row)) if row else None

    def list_facts(
        self, scope: MemoryScope, *, now: float | None = None, limit: int = 5
    ) -> list[MemoryFact]:
        if not isinstance(scope, MemoryScope):
            raise TypeError("trusted application scope required")
        if type(limit) is not int or not 1 <= limit <= 20:
            raise ValueError("limit must be in 1..20")
        timestamp = time.time() if now is None else float(now)
        rows = self.conn.execute("""
            SELECT key, value, source, revision, expires_at FROM memory_facts
            WHERE tenant_id=? AND user_id=?
              AND (expires_at IS NULL OR expires_at > ?)
            ORDER BY updated_at DESC, key ASC LIMIT ?
        """, (scope.tenant_id, scope.user_id, timestamp, limit)).fetchall()
        return [MemoryFact(**dict(row)) for row in rows]

    def forget(self, scope: MemoryScope, key: str) -> bool:
        if not isinstance(scope, MemoryScope):
            raise TypeError("trusted application scope required")
        with self.conn:
            result = self.conn.execute("""
                DELETE FROM memory_facts WHERE tenant_id=? AND user_id=? AND key=?
            """, (scope.tenant_id, scope.user_id, key))
        return result.rowcount == 1

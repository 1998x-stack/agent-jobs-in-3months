"""A09 micro-experiment: atomic scoped memory with SQLite."""
import sqlite3
from typing import Any


def solve(input_data: dict[str, Any]) -> dict[str, Any]:
    tenant = input_data.get("tenant")
    user = input_data.get("user")
    key = input_data.get("key")
    value = input_data.get("value")
    if not all(isinstance(v, str) and v.strip() for v in (tenant, user, key, value)):
        raise ValueError("tenant, user, key and value required")
    with sqlite3.connect(":memory:") as db:
        db.execute("""
            CREATE TABLE memory (
                tenant TEXT, user TEXT, key TEXT, value TEXT,
                PRIMARY KEY(tenant, user, key)
            )
        """)
        db.execute(
            "INSERT INTO memory(tenant, user, key, value) VALUES (?, ?, ?, ?)",
            (tenant, user, key, value),
        )
        db.commit()
        found = db.execute(
            "SELECT value FROM memory WHERE tenant=? AND user=? AND key=?",
            (tenant, user, key),
        ).fetchone()
        other = db.execute(
            "SELECT value FROM memory WHERE tenant=? AND user=? AND key=?",
            ("different-tenant", user, key),
        ).fetchone()
    return {"value": found[0], "other_tenant_value": other[0] if other else None}

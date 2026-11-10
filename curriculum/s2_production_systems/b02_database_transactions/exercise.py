"""B02: one SQLite transaction updates a task and its audit record atomically."""
import sqlite3
from typing import Any


def solve(input_data: dict[str, Any]) -> dict[str, Any]:
    failure = input_data.get("fail_audit", False)
    if type(failure) is not bool:
        raise ValueError("fail_audit must be boolean")
    with sqlite3.connect(":memory:", isolation_level=None) as db:
        db.execute("CREATE TABLE runs(id TEXT PRIMARY KEY)")
        db.execute("CREATE TABLE audits(id TEXT PRIMARY KEY REFERENCES runs(id))")
        committed = True
        try:
            db.execute("BEGIN IMMEDIATE")
            db.execute("INSERT INTO runs VALUES ('run-1')")
            if failure:
                raise RuntimeError("simulated failure before audit write")
            db.execute("INSERT INTO audits VALUES ('run-1')")
            db.execute("COMMIT")
        except RuntimeError:
            db.execute("ROLLBACK")
            committed = False
        return {
            "committed": committed,
            "runs": db.execute("SELECT COUNT(*) FROM runs").fetchone()[0],
            "audits": db.execute("SELECT COUNT(*) FROM audits").fetchone()[0],
        }

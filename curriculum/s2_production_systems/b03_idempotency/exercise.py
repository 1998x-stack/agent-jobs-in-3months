"""B03: stable idempotency key + fingerprint, demonstrating replay/conflict."""
import hashlib
import json
import sqlite3
from typing import Any


def solve(input_data: dict[str, Any]) -> dict[str, Any]:
    requests = input_data.get("requests")
    if not isinstance(requests, list) or not requests:
        raise ValueError("requests must be a nonempty list")
    created = 0
    replays = 0
    with sqlite3.connect(":memory:", isolation_level=None) as db:
        db.execute("CREATE TABLE keys(request_key TEXT PRIMARY KEY, fingerprint TEXT)")
        for item in requests:
            if not isinstance(item, dict) or set(item) != {"key", "payload"}:
                raise ValueError("request needs key and payload")
            if not isinstance(item["key"], str) or not item["key"]:
                raise ValueError("key required")
            fingerprint = hashlib.sha256(
                json.dumps(item["payload"], sort_keys=True).encode("utf-8")
            ).hexdigest()
            db.execute("BEGIN IMMEDIATE")
            found = db.execute(
                "SELECT fingerprint FROM keys WHERE request_key=?", (item["key"],)
            ).fetchone()
            if found is None:
                db.execute("INSERT INTO keys VALUES (?,?)", (item["key"], fingerprint))
                created += 1
            elif found[0] != fingerprint:
                db.execute("ROLLBACK")
                raise ValueError("409: idempotency key reused for different payload")
            else:
                replays += 1
            db.execute("COMMIT")
    return {"created": created, "replays": replays}

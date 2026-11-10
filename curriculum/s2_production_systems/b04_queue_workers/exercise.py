"""B04: compete for work using one SQLite file, one transaction per worker."""
from concurrent.futures import ThreadPoolExecutor
from tempfile import TemporaryDirectory
from pathlib import Path
import sqlite3
from typing import Any


def solve(input_data: dict[str, Any]) -> dict[str, Any]:
    jobs = input_data.get("jobs")
    workers = input_data.get("workers", 3)
    if not isinstance(jobs, list) or not all(
        isinstance(job, str) and job.strip() for job in jobs
    ) or len(jobs) > 16 or not jobs:
        raise ValueError("jobs must contain 1..16 nonempty strings")
    if type(workers) is not int or not 1 <= workers <= 8:
        raise ValueError("workers must be 1..8")
    with TemporaryDirectory() as directory:
        path = str(Path(directory) / "queue.sqlite3")
        with sqlite3.connect(path) as db:
            db.execute(
                "CREATE TABLE queue (id INTEGER PRIMARY KEY, job TEXT, state TEXT)"
            )
            db.executemany(
                "INSERT INTO queue(job,state) VALUES (?,'queued')",
                [(job,) for job in jobs],
            )

        def claim() -> int | None:
            with sqlite3.connect(path, isolation_level=None, timeout=10) as db:
                db.execute("BEGIN IMMEDIATE")
                row = db.execute(
                    "SELECT id FROM queue WHERE state='queued' ORDER BY id LIMIT 1"
                ).fetchone()
                if row is None:
                    db.execute("COMMIT")
                    return None
                db.execute(
                    "UPDATE queue SET state='running' WHERE id=?", (row[0],)
                )
                db.execute("COMMIT")
                return row[0]

        with ThreadPoolExecutor(max_workers=workers) as pool:
            taken = list(pool.map(lambda _: claim(), range(len(jobs) + workers)))
        delivered = [item for item in taken if item is not None]
        return {
            "jobs": len(jobs),
            "claims": len(delivered),
            "unique_claims": len(set(delivered)),
            "no_duplicate_claim": len(delivered) == len(set(delivered)),
        }

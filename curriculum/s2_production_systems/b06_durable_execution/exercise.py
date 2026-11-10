"""B06: persist a checkpoint in SQLite; after crash, resume remaining steps.

This shows step-level recovery, not exactly-once arbitrary external effects.
"""
from pathlib import Path
from tempfile import TemporaryDirectory
import sqlite3
from typing import Any


def solve(input_data: dict[str, Any]) -> dict[str, Any]:
    steps = input_data.get("steps", ["plan", "research", "review"])
    crash_after = input_data.get("crash_after", 1)
    if not isinstance(steps, list) or not 1 <= len(steps) <= 5 or not all(
        isinstance(step, str) and step.strip() for step in steps
    ):
        raise ValueError("steps must be 1..5 nonempty strings")
    if len(steps) != len(set(steps)):
        raise ValueError("step names must be unique")
    if type(crash_after) is not int or not 0 <= crash_after < len(steps):
        raise ValueError("crash_after must be a valid completed prefix length")

    with TemporaryDirectory() as directory:
        path = Path(directory) / "workflow.sqlite3"
        with sqlite3.connect(path) as db:
            db.execute("CREATE TABLE checkpoints (step TEXT PRIMARY KEY)")
            for step in steps[:crash_after]:
                db.execute("INSERT INTO checkpoints VALUES (?)", (step,))
        # Simulate process restart by reopening the same file.
        with sqlite3.connect(path) as db:
            completed = {row[0] for row in db.execute("SELECT step FROM checkpoints")}
            reused = [step for step in steps if step in completed]
            executed = []
            for step in steps:
                if step in completed:
                    continue
                db.execute("INSERT INTO checkpoints VALUES (?)", (step,))
                executed.append(step)
        return {"reused": reused, "executed": executed, "total": len(steps)}

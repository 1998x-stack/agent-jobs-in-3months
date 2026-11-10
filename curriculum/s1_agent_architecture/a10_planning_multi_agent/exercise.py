"""A10 micro-experiment: bounded planner / researcher / reviewer handoff plan.

This demonstrates role contracts. It is NOT an MCP implementation.
"""
import re
from typing import Any


_ALLOWED_TRANSITIONS = {("planner", "researcher"), ("researcher", "reviewer")}


def solve(input_data: dict[str, Any]) -> dict[str, Any]:
    goal = input_data.get("goal")
    max_tasks = input_data.get("max_tasks", 2)
    if not isinstance(goal, str) or not goal.strip():
        raise ValueError("goal required")
    if type(max_tasks) is not int or not 1 <= max_tasks <= 3:
        raise ValueError("max_tasks must be 1..3")
    tasks = [
        part.strip()
        for part in re.split(r"\s+and\s+|\s*;\s*", goal.strip())
        if part.strip()
    ]
    if len(tasks) > max_tasks:
        raise RuntimeError("subtask budget exhausted")
    handoffs = []
    for index, task in enumerate(tasks, start=1):
        task_id = f"task-{index:02d}"
        for source, target in (("planner", "researcher"), ("researcher", "reviewer")):
            if (source, target) not in _ALLOWED_TRANSITIONS:
                raise PermissionError("handoff not authorized")
            handoffs.append({"task_id": task_id, "from": source, "to": target})
    return {"task_count": len(tasks), "handoffs": handoffs}

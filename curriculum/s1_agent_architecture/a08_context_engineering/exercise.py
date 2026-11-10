"""A08 micro-experiment: pack provenance-labeled context within a fixed budget.

This uses an exact character budget, NOT model-specific token counting.
"""
import json
from typing import Any


def solve(input_data: dict[str, Any]) -> dict[str, Any]:
    goal = input_data.get("goal")
    instructions = input_data.get("instructions")
    blocks = input_data.get("blocks", [])
    max_chars = input_data.get("max_chars", 400)
    if not isinstance(goal, str) or not goal.strip():
        raise ValueError("goal required")
    if not isinstance(instructions, str) or not instructions.strip():
        raise ValueError("instructions required")
    if type(max_chars) is not int or max_chars <= 0 or not isinstance(blocks, list):
        raise ValueError("invalid budget or blocks")
    payload = {"instructions": instructions, "goal": goal, "untrusted_data": []}
    def serialize() -> str:
        return json.dumps(payload, ensure_ascii=False, sort_keys=True)
    if len(serialize()) > max_chars:
        raise ValueError("trusted core exceeds budget")
    kept, dropped = [], []
    for block in blocks:
        if not isinstance(block, dict) or set(block) != {"source_id", "content"}:
            raise ValueError("source_id and content are required")
        item = {"source_id": block["source_id"], "content": block["content"], "trust": "untrusted"}
        payload["untrusted_data"].append(item)
        if len(serialize()) > max_chars:
            payload["untrusted_data"].pop()
            dropped.append(block["source_id"])
        else:
            kept.append(block["source_id"])
    return {"context": serialize(), "selected_ids": kept, "dropped_ids": dropped}

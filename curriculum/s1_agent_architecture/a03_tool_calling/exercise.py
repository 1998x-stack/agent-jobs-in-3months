"""A03: only allow known, locally validated read-only tools."""
from typing import Any

def lookup_policy(*, topic: str) -> str:
    return {"refund": "Refund requires human approval."}.get(
        topic, "Policy unavailable; ask for clarification."
    )

TOOLS = {"lookup_policy": lookup_policy}

def solve(input_data: dict[str, Any]) -> dict[str, Any]:
    name = input_data.get("tool")
    args = input_data.get("arguments")
    if name not in TOOLS:
        raise PermissionError("tool name is not allowlisted")
    if not isinstance(args, dict) or set(args) != {"topic"}:
        raise ValueError("arguments must contain only topic")
    if not isinstance(args["topic"], str) or not args["topic"].strip():
        raise ValueError("invalid topic")
    return {"tool": name, "result": TOOLS[name](topic=args["topic"])}

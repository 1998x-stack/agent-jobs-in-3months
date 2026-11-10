"""A05: give tools explicit read-only contracts and distinct error semantics."""
from typing import Any


def solve(input_data: dict[str, Any]) -> dict[str, Any]:
    name = input_data.get("tool")
    args = input_data.get("arguments")
    if name != "lookup_policy":
        raise PermissionError("only the read-only lookup_policy tool is available")
    if not isinstance(args, dict) or set(args) != {"topic"}:
        raise ValueError("arguments must contain topic and no other fields")
    topic = args["topic"]
    if not isinstance(topic, str) or not topic.strip():
        raise ValueError("topic must be a nonempty string")
    policies = {"refund": "Every refund needs human approval."}
    if topic not in policies:
        return {"status": "no_evidence", "data": None}
    return {"status": "ok", "data": {"policy": policies[topic]}}

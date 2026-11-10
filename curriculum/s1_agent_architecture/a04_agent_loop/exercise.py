"""A04: an offline Observe-Decide-Act loop with explicit stopping semantics."""
from typing import Any

def solve(input_data: dict[str, Any]) -> dict[str, Any]:
    goal = input_data.get("goal")
    max_steps = input_data.get("max_steps", 3)
    actions = input_data.get("actions", [
        {"kind": "tool", "name": "lookup_policy", "arguments": {"topic": "refund"}},
        {"kind": "finish", "output": "Policy lookup complete."},
    ])
    if not isinstance(goal, str) or not goal.strip():
        raise ValueError("goal required")
    if type(max_steps) is not int or max_steps <= 0 or not isinstance(actions, list):
        raise ValueError("invalid steps or actions")
    trace = []
    for step, action in enumerate(actions[:max_steps], start=1):
        if action.get("kind") == "finish":
            return {"answer": action.get("output", ""), "trace": trace, "stop_reason": "finished"}
        if action.get("kind") != "tool" or action.get("name") != "lookup_policy":
            raise PermissionError("unknown or unauthorized action")
        args = action.get("arguments")
        if not isinstance(args, dict) or set(args) != {"topic"}:
            raise ValueError("invalid tool arguments")
        topic = args["topic"]
        if not isinstance(topic, str) or not topic.strip():
            raise ValueError("invalid topic")
        observation = "Refund requires human approval." if topic == "refund" else "Unknown policy."
        trace.append({"step": step, "tool": "lookup_policy", "observation": observation})
    raise RuntimeError("step budget exhausted before finish")

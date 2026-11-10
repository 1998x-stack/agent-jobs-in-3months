"""A01: construct a model request with explicit role and token limit."""
from typing import Any

def solve(input_data: dict[str, Any]) -> dict[str, Any]:
    goal = input_data.get("goal")
    budget = input_data.get("max_output_tokens", 1024)
    if not isinstance(goal, str) or not goal.strip():
        raise ValueError("goal required")
    if type(budget) is not int or not 1 <= budget <= 8192:
        raise ValueError("invalid token budget")
    return {
        "messages": [{"role": "user", "content": goal.strip()}],
        "max_output_tokens": budget,
        "stop_reason": "awaiting_model_response",
    }

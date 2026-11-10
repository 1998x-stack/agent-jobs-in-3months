"""C06: one-variable paired ablation comparison using stable task IDs."""
from typing import Any


def solve(input_data: dict[str, Any]) -> dict[str, Any]:
    control = input_data.get("control")
    variant = input_data.get("variant")
    changed_component = input_data.get("changed_component")
    if not isinstance(control, dict) or not isinstance(variant, dict) or not control:
        raise ValueError("paired case result maps required")
    if set(control) != set(variant):
        raise ValueError("the same task IDs must be present in both arms")
    if changed_component not in (
        "retrieval_evidence", "memory", "context_budget", "planner_decomposition",
    ):
        raise ValueError("one registered component must change")
    if any(type(x) is not bool for x in list(control.values()) + list(variant.values())):
        raise ValueError("success flags must be booleans")
    n = len(control)
    better = sum(not control[key] and variant[key] for key in control)
    worse = sum(control[key] and not variant[key] for key in control)
    delta = (sum(variant.values()) - sum(control.values())) / n
    return {
        "n": n,
        "changed_component": changed_component,
        "control_passed": sum(control.values()),
        "variant_passed": sum(variant.values()),
        "delta": delta,
        "wins": better,
        "losses": worse,
    }

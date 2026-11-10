"""Paired offline toy ablation; not representative of a real LLM."""
from .graders import grade
from .statistics import paired_delta_ci

def toy_run(case: dict, retrieval_enabled: bool) -> dict:
    needs_policy = "lookup_policy" in case["required_tools"]
    tool_calls = ["lookup_policy"] if retrieval_enabled and needs_policy else []
    outcome = case["expected_outcome"] if (not needs_policy or retrieval_enabled) else "unknown"
    return {"outcome": outcome, "tool_calls": tool_calls}

def compare(cases: list[dict]) -> dict:
    base = [grade(case, toy_run(case, False))["passed"] for case in cases]
    variant = [grade(case, toy_run(case, True))["passed"] for case in cases]
    delta, lo, hi = paired_delta_ci(base, variant)
    return {"n": len(cases), "baseline_pass": sum(base),
            "variant_pass": sum(variant), "delta": delta, "ci": [lo, hi]}

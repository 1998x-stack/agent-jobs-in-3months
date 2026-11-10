"""C02: an outcome oracle checks structured environment state, not prose."""
from typing import Any


def solve(input_data: dict[str, Any]) -> dict[str, Any]:
    expected = input_data.get("expected")
    actual = input_data.get("actual")
    if not isinstance(expected, dict) or not isinstance(actual, dict):
        raise ValueError("expected and actual state objects required")
    keys = {"run_status", "result_status", "receipt_count"}
    if set(expected) != keys or not keys.issubset(actual):
        raise ValueError("missing or unexpected state fields")
    if type(actual["receipt_count"]) is not int or actual["receipt_count"] < 0:
        raise ValueError("invalid receipt count")
    checks = {key: expected[key] == actual[key] for key in sorted(keys)}
    return {
        "passed": all(checks.values()),
        "checks": checks,
        "mismatches": [key for key, ok in checks.items() if not ok],
    }

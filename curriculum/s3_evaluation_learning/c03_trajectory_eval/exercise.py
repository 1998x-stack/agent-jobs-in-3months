"""C03: verify ordered tool names, forbidden actions and known parameters."""
from typing import Any


def is_subsequence(required: list[str], observed: list[str]) -> bool:
    sequence = iter(observed)
    return all(any(actual == step for actual in sequence) for step in required)


def solve(input_data: dict[str, Any]) -> dict[str, Any]:
    required = input_data.get("required_tools")
    forbidden = input_data.get("forbidden_tools", [])
    trace = input_data.get("trace")
    if not isinstance(required, list) or not isinstance(forbidden, list) or not isinstance(trace, list):
        raise ValueError("required_tools, forbidden_tools, trace must be lists")
    if any(not isinstance(item, str) for item in required + forbidden):
        raise ValueError("tool names must be strings")
    names = []
    for row in trace:
        if not isinstance(row, dict) or set(row) != {"name", "args"}:
            raise ValueError("each trace step requires name and args")
        if not isinstance(row["name"], str) or not (
            row["args"] is None or isinstance(row["args"], dict)
        ):
            raise ValueError("invalid observed step")
        names.append(row["name"])
    required_ok = is_subsequence(required, names)
    safety_ok = not set(forbidden).intersection(names)
    parameter_rule = input_data.get("expected_parameter")
    parameters_ok = True
    if parameter_rule is not None:
        if not isinstance(parameter_rule, dict) or set(parameter_rule) != {"tool", "key", "value"}:
            raise ValueError("parameter rule requires tool, key, value")
        parameters_ok = any(
            row["name"] == parameter_rule["tool"]
            and row["args"] is not None
            and row["args"].get(parameter_rule["key"]) == parameter_rule["value"]
            for row in trace
        )
    return {
        "passed": required_ok and safety_ok and parameters_ok,
        "required_ok": required_ok,
        "safety_ok": safety_ok,
        "parameters_ok": parameters_ok,
    }

"""B09: narrow sandbox contract, not arbitrary-code execution.

For actual fixed-code subprocess and resource caps see P2 sandbox.py.
"""
import hashlib
from typing import Any


def solve(input_data: dict[str, Any]) -> dict[str, Any]:
    operation = input_data.get("operation")
    data = input_data.get("data")
    if operation != "hash_text":
        raise PermissionError("only allowlisted pure tool is accepted")
    if not isinstance(data, str) or not data or len(data) > 512:
        raise ValueError("data must be 1..512 characters")
    if any(name in input_data for name in ("command", "shell", "env", "path")):
        raise PermissionError("arbitrary execution configuration is disallowed")
    return {
        "sha256": hashlib.sha256(data.encode("utf-8")).hexdigest(),
        "isolated_code_execution": False,
    }

"""B07: minimal four-eyes approval state machine. No external side effects."""
from typing import Any


def solve(input_data: dict[str, Any]) -> dict[str, Any]:
    requester = input_data.get("requester")
    reviewer = input_data.get("reviewer")
    executor = input_data.get("executor")
    decision = input_data.get("decision")
    if not all(isinstance(x, str) and x.strip() for x in (requester, reviewer, executor)):
        raise ValueError("three nonempty actor identities are required")
    if len({requester, reviewer, executor}) != 3:
        raise PermissionError("requester, reviewer and executor must be distinct")
    if decision not in ("approved", "denied", "pending"):
        raise ValueError("unknown decision")
    # No real or simulated side effect until the gate is approved.
    return {
        "approval_status": decision,
        "synthetic_receipt_allowed": decision == "approved",
        "requires_human_review": decision != "approved",
    }

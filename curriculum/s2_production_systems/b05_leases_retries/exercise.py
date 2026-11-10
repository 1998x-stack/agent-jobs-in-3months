"""B05: simulated lease expiry, fenced takeover and bounded exponential backoff."""
from typing import Any


def solve(input_data: dict[str, Any]) -> dict[str, Any]:
    lease = input_data.get("lease_seconds", 5)
    retry_attempt = input_data.get("retry_attempt", 2)
    if type(lease) not in (int, float) or not 0 < lease <= 3600:
        raise ValueError("lease must be positive and bounded")
    if type(retry_attempt) is not int or not 1 <= retry_attempt <= 3:
        raise ValueError("attempt must be in 1..3")
    first_owner = "token-A"
    lease_until = 100 + lease
    takeover_time = lease_until + 1
    second_owner = "token-B"
    # Conditional COMMIT must check both token and an unexpired lease.
    def can_commit(token: str, timestamp: float) -> bool:
        return token == second_owner and timestamp < takeover_time + lease
    delay = min(60.0, 2.0 * (2 ** (retry_attempt - 1)))
    return {
        "stale_committed": can_commit(first_owner, takeover_time),
        "fresh_committed": can_commit(second_owner, takeover_time),
        "backoff_seconds": delay,
        "final_attempt": retry_attempt == 3,
    }

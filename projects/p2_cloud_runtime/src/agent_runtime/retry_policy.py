"""B05: bounded exponential backoff; deterministic jitter for reproducible tests.

Automatic retry applies only to explicitly retryable failures. It never changes
the immutable HTTP request fingerprint or starts a second run.
"""
import hashlib
import math


class RetryableWorkError(RuntimeError):
    """A worker failure that is safe to retry because work is read-only."""


def retry_delay(
    attempt: int,
    *,
    base_seconds: float = 2.0,
    cap_seconds: float = 60.0,
    jitter_fraction: float = 0.0,
    seed: str = "",
) -> float:
    if type(attempt) is not int or not 1 <= attempt <= 32:
        raise ValueError("attempt must be in 1..32")
    if (
        not math.isfinite(base_seconds)
        or not math.isfinite(cap_seconds)
        or base_seconds <= 0
        or cap_seconds < base_seconds
    ):
        raise ValueError("invalid retry delay bounds")
    if not math.isfinite(jitter_fraction) or not 0 <= jitter_fraction <= 0.5:
        raise ValueError("jitter fraction must be in 0..0.5")
    delay = min(cap_seconds, base_seconds * (2 ** (attempt - 1)))
    if not jitter_fraction:
        return delay
    digest = hashlib.sha256(f"{seed}:{attempt}".encode()).digest()
    unit = int.from_bytes(digest[:8], "big") / (2**64 - 1)
    return delay * (1 - jitter_fraction * unit)

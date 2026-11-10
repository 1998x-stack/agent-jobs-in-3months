"""Lease specification extension point. Implement heartbeat and renewal."""
from dataclasses import dataclass

@dataclass(frozen=True)
class Lease:
    job_id: int
    token: str
    expires_at: float

def is_expired(lease: Lease, now: float) -> bool:
    return lease.expires_at <= now

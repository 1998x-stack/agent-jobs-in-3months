"""Explicit workflow transition policy for future worker orchestration."""
ALLOWED = {
    "queued": {"running", "cancelled"},
    "running": {"queued", "awaiting_approval", "completed", "failed"},
    "awaiting_approval": {"completed", "rejected"},
    "failed": {"queued"},
    "completed": set(),
    "rejected": set(),
    "cancelled": set(),
}

def validate_transition(old: str, new: str) -> None:
    if new not in ALLOWED.get(old, set()):
        raise ValueError(f"invalid transition: {old} -> {new}")

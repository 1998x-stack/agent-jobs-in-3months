"""Teaching-only context selector; replace with token-aware compaction."""
from typing import Any

def recent_observations(observations: list[Any], max_items: int = 5) -> list[Any]:
    if max_items < 0:
        raise ValueError("max_items must be non-negative")
    return observations[-max_items:] if max_items else []

"""Per-tenant in-process memory for teaching isolation, not persistence."""
from typing import Any

class MemoryStore:
    def __init__(self) -> None:
        self._items: dict[tuple[str, str], Any] = {}

    def put(self, tenant_id: str, key: str, value: Any) -> None:
        if not tenant_id:
            raise ValueError("tenant_id is required")
        self._items[(tenant_id, key)] = value

    def get(self, tenant_id: str, key: str) -> Any:
        return self._items.get((tenant_id, key))

"""Explicit tool registry: model-proposed tool names are not trusted."""
from collections.abc import Callable
from typing import Any

class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Callable[..., Any]] = {}

    def register(self, name: str, callback: Callable[..., Any]) -> None:
        if not name or name in self._tools:
            raise ValueError("tool name must be unique and non-empty")
        self._tools[name] = callback

    def execute(self, name: str, arguments: dict[str, Any]) -> Any:
        if name not in self._tools:
            raise PermissionError(f"Tool not allowed: {name}")
        return self._tools[name](**arguments)

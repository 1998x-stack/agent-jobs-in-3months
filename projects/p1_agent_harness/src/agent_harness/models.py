"""Typed interfaces for a deliberately minimal agent loop."""
from dataclasses import dataclass, field
from typing import Any, Literal

@dataclass(frozen=True)
class Action:
    kind: Literal["tool", "finish"]
    name: str = ""
    arguments: dict[str, Any] = field(default_factory=dict)
    output: str = ""

@dataclass(frozen=True)
class TraceStep:
    step: int
    action: str
    observation: Any

@dataclass(frozen=True)
class AgentResult:
    output: str
    trace: list[TraceStep]

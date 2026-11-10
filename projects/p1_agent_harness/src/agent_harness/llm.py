"""Provider-neutral LLM turn contract for A01 and A04.

This module deliberately does not depend on a model SDK.
It is possible to test the entire agent loop without API access.
"""
from dataclasses import dataclass
from typing import Protocol


class ModelProtocolError(RuntimeError):
    """The model response violates the one-tool-per-turn contract."""


class AgentBudgetExceeded(RuntimeError):
    """The agent exceeded a fixed model-turn or tool-execution budget."""


@dataclass(frozen=True)
class ToolProposal:
    call_id: str
    name: str
    arguments_json: str


@dataclass(frozen=True)
class ToolFeedback:
    call_id: str
    output: str


@dataclass(frozen=True)
class ModelTurn:
    response_id: str
    tool_calls: tuple[ToolProposal, ...] = ()
    final_text: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None


class ModelAdapter(Protocol):
    """One turn = one model API request. Feedback follows a previous response."""

    def create_turn(
        self,
        *,
        goal: str | None,
        feedback: ToolFeedback | None,
        previous_response_id: str | None,
        tool_definitions: list[dict],
    ) -> ModelTurn:
        ...

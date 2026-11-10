"""A02/A03: fail-closed allowlisted tool registry with Pydantic arguments."""
import json
import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, ValidationError

from .llm import ToolProposal


class InvalidToolArguments(ValueError):
    """Malformed JSON or tool arguments that do not match the declared schema."""


@dataclass(frozen=True)
class TypedTool:
    name: str
    description: str
    arguments: type[BaseModel]
    callback: Callable[..., Any]
    read_only: bool = True

    def as_responses_tool(self) -> dict:
        schema = self.arguments.model_json_schema()
        if schema.get("type") != "object" or schema.get("additionalProperties") is not False:
            raise ValueError("tool schema must be a strict object with extra='forbid'")
        return {
            "type": "function",
            "name": self.name,
            "description": self.description,
            "parameters": schema,
            "strict": True,
        }


class ValidatedToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, TypedTool] = {}

    def register(
        self,
        name: str,
        description: str,
        arguments: type[BaseModel],
        callback: Callable[..., Any],
        *,
        read_only: bool = True,
    ) -> None:
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
            raise ValueError("invalid tool name")
        if name in self._tools:
            raise ValueError("duplicate tool")
        if not issubclass(arguments, BaseModel):
            raise TypeError("arguments must be a Pydantic model class")
        if not callable(callback):
            raise TypeError("callback must be callable")
        tool = TypedTool(name, description, arguments, callback, read_only)
        tool.as_responses_tool()  # Fail early on non-strict or unsupported shape.
        self._tools[name] = tool

    def definitions(self) -> list[dict]:
        # Never offer write-enabled tools to this teaching agent.
        return [tool.as_responses_tool() for tool in self._tools.values() if tool.read_only]

    def execute(self, call: ToolProposal) -> str:
        tool = self._tools.get(call.name)
        if tool is None or not tool.read_only:
            raise PermissionError("tool unavailable or not authorized for read-only execution")
        try:
            raw = json.loads(call.arguments_json)
        except (json.JSONDecodeError, TypeError) as exc:
            raise InvalidToolArguments("arguments are not valid JSON") from exc
        if not isinstance(raw, dict):
            raise InvalidToolArguments("arguments must be a JSON object")
        try:
            arguments = tool.arguments.model_validate(raw)
        except ValidationError as exc:
            # Do not log raw model arguments: they may be sensitive.
            raise InvalidToolArguments("arguments failed Pydantic validation") from exc
        output = tool.callback(**arguments.model_dump())
        try:
            encoded = json.dumps({"result": output}, ensure_ascii=False)
        except (TypeError, ValueError) as exc:
            raise InvalidToolArguments("tool output is not JSON serializable") from exc
        if len(encoded) > 8000:
            raise InvalidToolArguments("tool output exceeds the 8000-character budget")
        return encoded

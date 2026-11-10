"""A02: parse untrusted JSON with local Pydantic validation."""
from typing import Any
from pydantic import BaseModel, ConfigDict, field_validator

class LookupPolicyArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")
    topic: str

    @field_validator("topic")
    @classmethod
    def valid_topic(cls, value):
        if not value.strip() or len(value) > 128:
            raise ValueError("topic out of range")
        return value.strip()

def solve(input_data: dict[str, Any]) -> dict[str, Any]:
    raw = input_data.get("arguments_json")
    if not isinstance(raw, str):
        raise ValueError("arguments_json must be a JSON string")
    args = LookupPolicyArguments.model_validate_json(raw)
    return {
        "tool_name": "lookup_policy",
        "arguments": args.model_dump(),
        "schema": LookupPolicyArguments.model_json_schema(),
    }

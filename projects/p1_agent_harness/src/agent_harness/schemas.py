"""A02: Pydantic input validation with strict object JSON Schema.

Keep min/max constraints in local validators because the API's strict schema
subset does not support every JSON Schema validation keyword.
"""
from pydantic import BaseModel, ConfigDict, field_validator


class StrictToolArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PolicyLookupArgs(StrictToolArgs):
    topic: str

    @field_validator("topic")
    @classmethod
    def validate_topic(cls, value: str) -> str:
        if not value.strip() or len(value) > 128:
            raise ValueError("topic must contain 1 to 128 characters")
        return value.strip()

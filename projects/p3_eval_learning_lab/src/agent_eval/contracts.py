"""C01: strict, versioned synthetic agent-evaluation dataset contract.

The split and source group are mandatory to avoid evaluating on training clones.
No user records or model/private traces belong in these files.
"""
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


SCHEMA_VERSION = "agent-eval.v1"
_ID = re.compile(r"^[a-z][a-z0-9_-]{2,63}$")
_CHUNK = re.compile(r"^[a-z][a-z0-9_]*:p[0-9]{2}$")
_ACTION = re.compile(r"^[a-z][a-z0-9_]{1,63}$")
_STEP = re.compile(r"^(plan|task-0[1-3])$")


class GoldState(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    run_status: Literal["completed", "failed"]
    result_status: Literal["supported", "partial", "insufficient_evidence"] | None = None
    required_citations: list[str] = Field(default_factory=list, max_length=4)
    required_checkpoints: list[str] = Field(default_factory=list, max_length=4)
    receipt_count: int = Field(default=0, ge=0, le=1)

    @model_validator(mode="after")
    def consistency(self) -> "GoldState":
        if len(set(self.required_citations)) != len(self.required_citations):
            raise ValueError("duplicate gold citations")
        if len(set(self.required_checkpoints)) != len(self.required_checkpoints):
            raise ValueError("duplicate gold checkpoints")
        if not all(_CHUNK.fullmatch(c) for c in self.required_citations):
            raise ValueError("invalid gold chunk ID")
        if not all(_STEP.fullmatch(step) for step in self.required_checkpoints):
            raise ValueError("invalid checkpoint key")
        if self.run_status == "failed" and self.result_status is not None:
            raise ValueError("a failed run cannot have a supported result")
        if self.result_status == "insufficient_evidence" and self.required_citations:
            raise ValueError("an abstention cannot require citations")
        return self


class ToolConstraint(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    name: str
    arguments_subset: dict[str, str | int | bool] = Field(default_factory=dict)

    @field_validator("name")
    @classmethod
    def valid_tool_name(cls, value: str) -> str:
        if not _ACTION.fullmatch(value):
            raise ValueError("unsafe tool name")
        return value


class EvalCase(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    schema_version: Literal["agent-eval.v1"]
    case_id: str
    split: Literal["train", "dev", "holdout"]
    group_id: str
    scenario: Literal[
        "policy_approval", "refund_timing", "shipping",
        "account_recovery", "cancellation", "abstention", "tenant_isolation",
    ]
    tenant: str = Field(min_length=1, max_length=64)
    question: str = Field(min_length=1, max_length=600)
    max_tasks: int = Field(default=1, ge=1, le=3)
    gold: GoldState
    required_tools: list[str] = Field(default_factory=list, max_length=6)
    forbidden_tools: list[str] = Field(default_factory=list, max_length=6)
    required_tool_arguments: list[ToolConstraint] = Field(default_factory=list)
    tags: list[str] = Field(min_length=1, max_length=5)

    @field_validator("case_id", "group_id")
    @classmethod
    def valid_id(cls, value: str) -> str:
        if not _ID.fullmatch(value):
            raise ValueError("case/group IDs must be lower-case stable identifiers")
        return value

    @field_validator("required_tools", "forbidden_tools")
    @classmethod
    def valid_actions(cls, values: list[str]) -> list[str]:
        if len(values) != len(set(values)) or not all(_ACTION.fullmatch(v) for v in values):
            raise ValueError("duplicate or invalid action")
        return values

    @field_validator("tags")
    @classmethod
    def valid_tags(cls, values: list[str]) -> list[str]:
        if len(values) != len(set(values)) or not all(_ID.fullmatch(tag) for tag in values):
            raise ValueError("duplicate or invalid tag")
        return values

    @model_validator(mode="after")
    def require_consistent_tools(self) -> "EvalCase":
        if set(self.required_tools) & set(self.forbidden_tools):
            raise ValueError("tool cannot be both required and forbidden")
        if not set(rule.name for rule in self.required_tool_arguments).issubset(
            set(self.required_tools)
        ):
            raise ValueError("argument constraints require corresponding tool")
        if self.scenario == "abstention" and self.gold.result_status != "insufficient_evidence":
            raise ValueError("abstention scenario requires abstention gold state")
        return self


def load_benchmark(path: str | Path) -> tuple[EvalCase, ...]:
    """Reject malformed JSON, duplicates, and cross-split group/question leakage."""
    cases: list[EvalCase] = []
    seen_ids: set[str] = set()
    groups: dict[str, str] = {}
    question_splits: dict[str, str] = {}
    with Path(path).open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                case = EvalCase.model_validate_json(line)
            except Exception as exc:
                raise ValueError(f"invalid benchmark line {line_number}") from exc
            if case.case_id in seen_ids:
                raise ValueError(f"duplicate case id: {case.case_id}")
            seen_ids.add(case.case_id)
            existing = groups.setdefault(case.group_id, case.split)
            if existing != case.split:
                raise ValueError(f"cross-split group contamination: {case.group_id}")
            normalized = " ".join(case.question.casefold().split())
            earlier = question_splits.setdefault(normalized, case.split)
            if earlier != case.split:
                raise ValueError("cross-split exact question contamination")
            cases.append(case)
    if not cases:
        raise ValueError("empty benchmark")
    return tuple(cases)


def benchmark_digest(cases: tuple[EvalCase, ...]) -> str:
    """Stable content fingerprint: changes if any gold label changes."""
    canonical = json.dumps(
        [case.model_dump(mode="json") for case in sorted(cases, key=lambda c: c.case_id)],
        sort_keys=True, separators=(",", ":"), ensure_ascii=False,
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


def coverage(cases: tuple[EvalCase, ...]) -> dict:
    by_split: dict[str, int] = {}
    by_scenario: dict[str, int] = {}
    for case in cases:
        by_split[case.split] = by_split.get(case.split, 0) + 1
        by_scenario[case.scenario] = by_scenario.get(case.scenario, 0) + 1
    return {
        "total": len(cases),
        "splits": dict(sorted(by_split.items())),
        "scenarios": dict(sorted(by_scenario.items())),
        "digest_sha256": benchmark_digest(cases),
    }

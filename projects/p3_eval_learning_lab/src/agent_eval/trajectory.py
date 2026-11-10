"""C03: process-level trajectory scoring with no raw observations.

P1 adapter: actual TraceStep tool names (arguments were not recorded).
P2 adapter: reconstruction from committed checkpoint sequence + stored A04
tool action names. This is NOT an exact timestamped full event stream.
Unknown arguments remain None; parameter constraints fail closed.
"""
from dataclasses import dataclass
import json
import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from agent_harness.models import AgentResult
from agent_harness.scoped_memory import MemoryScope
from agent_runtime.run_repository import RunRepository

from .contracts import EvalCase


_NAME = re.compile(r"^[a-z][a-z0-9_:-]{0,63}$")


class TraceEvent(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    index: int = Field(ge=1)
    kind: Literal["tool_call", "checkpoint", "run_state"]
    name: str
    origin: Literal["p1_agent_loop", "p2_checkpoint", "p2_run_state"]
    # None means arguments are NOT OBSERVED, rather than empty arguments.
    arguments: dict[str, str | int | bool] | None = None

    @field_validator("name")
    @classmethod
    def safe_name(cls, name: str) -> str:
        if not _NAME.fullmatch(name):
            raise ValueError("unsafe trace name")
        return name


@dataclass(frozen=True)
class TrajectoryReport:
    passed: bool
    checks: dict[str, bool]
    failure_codes: tuple[str, ...]
    inspected_tool_calls: int
    arguments_observed: bool


def from_p1_result(result: AgentResult) -> tuple[TraceEvent, ...]:
    """Observed tool names; NEVER serialize P1 observation or source text."""
    if not isinstance(result, AgentResult):
        raise TypeError("P1 AgentResult required")
    return tuple(TraceEvent(
        index=index, kind="tool_call", name=step.action,
        origin="p1_agent_loop", arguments=None,
    ) for index, step in enumerate(result.trace, 1))


def from_p2_run(
    repository: RunRepository, *,
    scope: MemoryScope, run_id: str,
) -> tuple[TraceEvent, ...]:
    """Read actor-owned persisted checkpoints, reconstruct task-step order.

    Only tool *names*, not their arguments, are persisted by the P1/P2 bridge.
    A checkpoint is definitive evidence the associated subtask completed,
    but no claims are made about undocumented individual model turns.
    """
    run = repository.get(scope, run_id)
    if run is None:
        raise PermissionError("run not visible to this actor")
    with repository._connect() as db:
        rows = db.execute("""
            SELECT step_key, payload_json FROM run_checkpoints
            WHERE run_id=? ORDER BY
            CASE WHEN step_key='plan' THEN 0 ELSE 1 END, step_key
        """, (run_id,)).fetchall()
    events: list[TraceEvent] = []
    for row in rows:
        step_key = row["step_key"]
        payload = json.loads(row["payload_json"])
        if not isinstance(payload, dict):
            raise ValueError("corrupt checkpoint")
        if step_key != "plan":
            tools = payload.get("tool_actions", [])
            if not isinstance(tools, list) or any(not isinstance(t, str) for t in tools):
                raise ValueError("corrupt observed tool names")
            for tool_name in tools:
                events.append(TraceEvent(
                    index=len(events) + 1, kind="tool_call",
                    name=tool_name, origin="p2_checkpoint", arguments=None,
                ))
        events.append(TraceEvent(
            index=len(events) + 1, kind="checkpoint",
            name=step_key, origin="p2_checkpoint",
        ))
    events.append(TraceEvent(
        index=len(events) + 1, kind="run_state",
        name=run.status, origin="p2_run_state",
    ))
    return tuple(events)


def _subsequence(needed: list[str], actual: list[str]) -> bool:
    iterator = iter(actual)
    return all(any(candidate == item for candidate in iterator) for item in needed)


def grade_trajectory(
    case: EvalCase,
    events: tuple[TraceEvent, ...] | list[TraceEvent],
) -> TrajectoryReport:
    if not isinstance(case, EvalCase):
        raise TypeError("validated EvalCase required")
    if not isinstance(events, (tuple, list)):
        raise ValueError("trace must be a sequence")
    if any(not isinstance(event, TraceEvent) for event in events):
        raise ValueError("trace must have validated TraceEvents")
    seq = [event.index for event in events]
    order_ok = seq == list(range(1, len(seq) + 1))
    tools = [e.name for e in events if e.kind == "tool_call"]
    checkpoint_names = [e.name for e in events if e.kind == "checkpoint"]
    states = [e.name for e in events if e.kind == "run_state"]
    safe = not bool(set(tools) & set(case.forbidden_tools))
    required_ok = _subsequence(case.required_tools, tools)
    checkpoint_ok = _subsequence(case.gold.required_checkpoints, checkpoint_names)
    state_ok = bool(states) and states == [case.gold.run_status] and events[-1].kind == "run_state" if events else False
    arg_ok = True
    observed = True
    for constraint in case.required_tool_arguments:
        candidates = [
            e for e in events
            if e.kind == "tool_call" and e.name == constraint.name
        ]
        if not candidates or not any(
            e.arguments is not None and all(
                e.arguments.get(key) == value and
                type(e.arguments.get(key)) is type(value)
                for key, value in constraint.arguments_subset.items()
            ) for e in candidates
        ):
            arg_ok = False
        if candidates and all(e.arguments is None for e in candidates):
            observed = False

    checks = {
        "trace_structure_ok": order_ok,
        "forbidden_tools_ok": safe,
        "required_tools_ok": required_ok,
        "tool_arguments_ok": arg_ok,
        "checkpoints_ok": checkpoint_ok,
        "terminal_state_ok": state_ok,
    }
    return TrajectoryReport(
        passed=all(checks.values()),
        checks=checks,
        failure_codes=tuple(key for key, ok in checks.items() if not ok),
        inspected_tool_calls=len(tools),
        arguments_observed=observed,
    )


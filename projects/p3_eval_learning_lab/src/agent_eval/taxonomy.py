"""Deterministic first-failure taxonomy; labels describe checks, not causality."""
from dataclasses import dataclass

from .state_oracle import OracleReport
from .trajectory import TrajectoryReport


_PRIORITIES = (
    ("forbidden_tools_ok", "unsafe_tool"),
    ("run_status_ok", "wrong_run_state"),
    ("receipt_count_ok", "side_effect_mismatch"),
    ("result_status_ok", "wrong_result_state"),
    ("citations_ok", "citation_mismatch"),
    ("required_tools_ok", "missing_or_misordered_tool"),
    ("tool_arguments_ok", "tool_parameter_mismatch"),
    ("checkpoints_ok", "checkpoint_mismatch"),
    ("terminal_state_ok", "terminal_trace_mismatch"),
    ("trace_structure_ok", "malformed_trajectory"),
)


@dataclass(frozen=True)
class FailureDiagnosis:
    primary: str
    all_failure_codes: tuple[str, ...]


def diagnose(oracle: OracleReport, trajectory: TrajectoryReport) -> FailureDiagnosis:
    checks = {**oracle.checks, **trajectory.checks}
    checks["checkpoints_ok"] = (
        oracle.checks.get("checkpoints_ok", False)
        and trajectory.checks.get("checkpoints_ok", False)
    )
    failures = tuple(
        category for check, category in _PRIORITIES if not checks.get(check, True)
    )
    return FailureDiagnosis(failures[0] if failures else "passed", failures)


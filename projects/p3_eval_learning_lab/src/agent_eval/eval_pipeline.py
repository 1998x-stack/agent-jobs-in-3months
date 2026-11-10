"""C01–C03: reproducible P1 + P2 read-only offline benchmark.

Per case: submit an actual P2 run; execute P1 through P2 worker; inspect
committed SQLite state and source-observed tool/checkpoint trace; score both.
No fabricated trace events, raw prompts in output or live model expenses.
"""
from dataclasses import dataclass
from pathlib import Path
import tempfile
from typing import Literal

from agent_harness.scoped_memory import MemoryScope
from agent_runtime.run_repository import RunRepository
from agent_runtime.task_worker import process_one

from .contracts import EvalCase, benchmark_digest, coverage, load_benchmark
from .state_oracle import grade_state, observe_state
from .taxonomy import diagnose
from .trajectory import from_p2_run, grade_trajectory


@dataclass(frozen=True)
class CaseScore:
    case_id: str
    split: str
    scenario: str
    passed: bool
    oracle_passed: bool
    trajectory_passed: bool
    tool_call_count: int
    failure_label: str
    failure_codes: tuple[str, ...]


def replay_case(case: EvalCase) -> CaseScore:
    """A fresh temporary DB guarantees isolation of each deterministic replay."""
    if not isinstance(case, EvalCase):
        raise TypeError("validated EvalCase required")
    with tempfile.TemporaryDirectory(prefix="agent-eval-") as temp:
        repo = RunRepository(Path(temp) / "run.sqlite3")
        scope = MemoryScope(case.tenant, "synthetic-eval-user")
        run, created = repo.submit(
            scope, idempotency_key="eval-" + case.case_id,
            question=case.question, max_tasks=case.max_tasks,
        )
        if not created:
            raise RuntimeError("unexpected duplicate test run")
        processed_id = process_one(repo)
        if processed_id != run.run_id:
            raise RuntimeError("offline worker did not process the benchmark run")
        actual = observe_state(repo, scope=scope, run_id=run.run_id)
        events = from_p2_run(repo, scope=scope, run_id=run.run_id)
        oracle = grade_state(case.gold, actual)
        process = grade_trajectory(case, events)
        diagnosis = diagnose(oracle, process)
        return CaseScore(
            case_id=case.case_id,
            split=case.split,
            scenario=case.scenario,
            passed=oracle.passed and process.passed,
            oracle_passed=oracle.passed,
            trajectory_passed=process.passed,
            tool_call_count=process.inspected_tool_calls,
            failure_label=diagnosis.primary,
            failure_codes=diagnosis.all_failure_codes,
        )


def evaluate(
    path: str | Path,
    *,
    split: Literal["train", "dev", "holdout"] | None = None,
) -> dict:
    cases = load_benchmark(path)
    selected = [case for case in cases if split is None or case.split == split]
    if not selected:
        raise ValueError("no cases in requested split")
    reports = [replay_case(case) for case in selected]
    passed = sum(item.passed for item in reports)
    failures: dict[str, int] = {}
    by_scenario: dict[str, dict] = {}
    for item in reports:
        if not item.passed:
            failures[item.failure_label] = failures.get(item.failure_label, 0) + 1
        bucket = by_scenario.setdefault(item.scenario, {"n": 0, "passed": 0})
        bucket["n"] += 1
        bucket["passed"] += int(item.passed)
    return {
        "schema_version": "agent-eval-report.v1",
        "dataset_digest_sha256": benchmark_digest(cases),
        "dataset_coverage": coverage(cases),
        "evaluated_split": split or "all",
        "n": len(reports),
        "passed": passed,
        "pass_rate": round(passed / len(reports), 4),
        "oracle_passed": sum(item.oracle_passed for item in reports),
        "trajectory_passed": sum(item.trajectory_passed for item in reports),
        "by_scenario": dict(sorted(by_scenario.items())),
        "failure_distribution": dict(sorted(failures.items())),
        "cases": [
            {
                "case_id": item.case_id,
                "passed": item.passed,
                "failure_label": item.failure_label,
                "failure_codes": list(item.failure_codes),
                "observed_tool_calls": item.tool_call_count,
            }
            for item in reports
        ],
    }


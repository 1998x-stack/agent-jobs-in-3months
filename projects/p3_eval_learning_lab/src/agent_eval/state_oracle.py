"""C02: database-backed gold state oracle, not an LLM-as-judge.

Reads the *actual* actor-owned P2 run, saved checkpoints and synthetic receipt
count. It does not treat a model's assertion of successful execution as truth.
No mutation, private prompts, tokens or freeform errors in the grade report.
"""
from dataclasses import dataclass

from agent_harness.scoped_memory import MemoryScope
from agent_runtime.run_repository import RunRepository

from .contracts import GoldState


@dataclass(frozen=True)
class ObservedState:
    run_status: str
    result_status: str | None
    citation_ids: tuple[str, ...]
    checkpoint_keys: tuple[str, ...]
    receipt_count: int


@dataclass(frozen=True)
class OracleReport:
    passed: bool
    checks: dict[str, bool]
    failure_codes: tuple[str, ...]


def observe_state(
    repository: RunRepository,
    *,
    scope: MemoryScope,
    run_id: str,
) -> ObservedState:
    if not isinstance(scope, MemoryScope):
        raise TypeError("trusted scope required")
    run = repository.get(scope, run_id)
    if run is None:
        raise PermissionError("run is not visible to actor")
    result = run.result
    if result is not None and not isinstance(result, dict):
        raise ValueError("corrupt result shape")
    citations = result.get("citation_ids", []) if result else []
    if not isinstance(citations, list) or any(not isinstance(x, str) for x in citations):
        raise ValueError("invalid saved citations")
    keys = repository.checkpoint_keys(run_id)  # only after actor ownership check
    with repository._connect() as db:
        tables = {
            row["name"]
            for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        receipt_count = 0
        if {"approvals_v2", "approval_receipts"}.issubset(tables):
            receipt_count = int(db.execute("""
                SELECT COUNT(*) FROM approval_receipts receipts
                JOIN approvals_v2 approvals ON approvals.approval_id=receipts.approval_id
                WHERE approvals.run_id=? AND approvals.tenant_id=?
            """, (run_id, scope.tenant_id)).fetchone()[0])
    return ObservedState(
        run_status=run.status,
        result_status=result.get("status") if result else None,
        citation_ids=tuple(citations),
        checkpoint_keys=keys,
        receipt_count=receipt_count,
    )


def grade_state(gold: GoldState, actual: ObservedState) -> OracleReport:
    checks = {
        "run_status_ok": actual.run_status == gold.run_status,
        "result_status_ok": actual.result_status == gold.result_status,
        "citations_ok": set(gold.required_citations).issubset(actual.citation_ids),
        "checkpoints_ok": set(gold.required_checkpoints).issubset(actual.checkpoint_keys),
        "receipt_count_ok": actual.receipt_count == gold.receipt_count,
    }
    # Abstention must not contain fabricated or unrelated citations.
    if gold.result_status == "insufficient_evidence" and actual.citation_ids:
        checks["citations_ok"] = False
    if gold.run_status == "failed" and actual.result_status is not None:
        checks["result_status_ok"] = False
    return OracleReport(
        passed=all(checks.values()),
        checks=checks,
        failure_codes=tuple(key for key, ok in checks.items() if not ok),
    )

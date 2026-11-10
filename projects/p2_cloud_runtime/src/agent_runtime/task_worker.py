"""B01-B03: standalone offline worker integrating P1 team with P2 task storage.

No LLM/API keys, no side-effecting tools; model used is deterministic.
Claim-fencing prevents stale result COMMIT, but is not exactly-once execution
after a timeout. External write operations need P2 outbox + reconciliation.
"""
import argparse
import json
from pathlib import Path
import time
from typing import Callable

from agent_harness.agent_team import TeamCoordinator
from agent_harness.policy_search import PolicyCorpus, demo_corpus
from agent_harness.scoped_memory import MemoryScope, ScopedMemoryStore

from .run_repository import RunRecord, RunRepository


def offline_executor(run: RunRecord, *, db_path: str, corpus: PolicyCorpus) -> dict:
    scope = MemoryScope(run.tenant_id, run.user_id)
    with ScopedMemoryStore(db_path) as memory:
        team = TeamCoordinator(corpus, memory)
        result = team.run(
            run.question, scope=scope,
            max_tasks=run.max_tasks,
            max_context_chars=run.max_context_chars,
        )
    return {
        "status": result.status,
        "answer": result.text,
        "citation_ids": list(result.citation_ids),
        "handoff_count": len(result.handoffs),
    }


def process_one(
    repository: RunRepository,
    *,
    corpus: PolicyCorpus | None = None,
    executor: Callable[[RunRecord], dict] | None = None,
    now: float | None = None,
    lease_seconds: float = 120.0,
) -> str | None:
    """One task per call. Failures are sanitized to an error code, not raw traceback."""
    claim = repository.claim_next(now=now, lease_seconds=lease_seconds)
    if claim is None:
        return None
    try:
        if executor is not None:
            result = executor(claim.run)
        else:
            result = offline_executor(
                claim.run, db_path=repository.filename,
                corpus=corpus if corpus is not None else demo_corpus(),
            )
    except Exception:
        repository.fail(claim, error_code="worker_failed", now=now)
        return claim.run.run_id
    if not repository.complete(claim, result, now=now):
        # Fencing prevents old workers from committing a late result.
        raise RuntimeError("stale or expired worker claim: result was not committed")
    return claim.run.run_id


def main() -> None:
    parser = argparse.ArgumentParser(description="P2 offline one-task worker")
    parser.add_argument("--db", default="./agent-runs.sqlite3")
    args = parser.parse_args()
    repository = RunRepository(args.db)
    run_id = process_one(repository)
    print("processed:", run_id if run_id else "none queued")


if __name__ == "__main__":
    main()

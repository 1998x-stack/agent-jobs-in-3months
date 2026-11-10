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

from .observability import SafeEvent, SafeTelemetry
from .durable_workflow import DurableWorkflow
from .retry_policy import RetryableWorkError
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
    after_checkpoint: Callable[[str], None] | None = None,
    telemetry: SafeTelemetry | None = None,
    split_plan: bool = True,
) -> str | None:
    """One task per call. Failures are sanitized to an error code, not raw traceback."""
    claim = repository.claim_next(now=now, lease_seconds=lease_seconds)
    if claim is None:
        return None
    started = time.perf_counter()

    def record(outcome: str) -> None:
        if telemetry is not None:
            telemetry.record(SafeEvent(
                operation="worker_run",
                outcome=outcome,
                duration_ms=(time.perf_counter() - started) * 1000,
                attempt=claim.run.attempt,
            ))

    try:
        if executor is not None:
            result = executor(claim.run)
        else:
            result = DurableWorkflow(
                repository,
                corpus=corpus if corpus is not None else demo_corpus(),
                after_checkpoint=after_checkpoint,
                split_plan=split_plan,
            ).execute(claim, now=now).result
    except RetryableWorkError:
        # Retry only errors explicitly classified as transient. These
        # teaching tools are READ ONLY; external writes need an outbox.
        repository.schedule_retry(claim, now=now, jitter_fraction=0.2)
        record("error")
        return claim.run.run_id
    except Exception:
        repository.fail(claim, error_code="worker_failed", now=now)
        record("error")
        return claim.run.run_id
    if not repository.complete(claim, result, now=now):
        # Fencing prevents old workers from committing a late result.
        record("error")
        raise RuntimeError("stale or expired worker claim: result was not committed")
    record("ok")
    return claim.run.run_id


def main() -> None:
    parser = argparse.ArgumentParser(description="P2 offline one-task worker")
    parser.add_argument("--db", default="./agent-runs.sqlite3")
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--max-jobs", type=int, default=1)
    parser.add_argument("--poll", action="store_true", help="keep polling until Ctrl+C")
    args = parser.parse_args()
    repository = RunRepository(args.db)
    from .worker_pool import poll_batches, run_batch
    if args.poll:
        from threading import Event
        stop = Event()
        try:
            poll_batches(
                repository, stop, parallelism=args.workers,
                batch_size=args.max_jobs,
            )
        except KeyboardInterrupt:
            stop.set()
    else:
        report = run_batch(
            repository, parallelism=args.workers, max_jobs=args.max_jobs
        )
        print("processed:", list(report.processed_run_ids))
    print("queue:", repository.queue_stats())


if __name__ == "__main__":
    main()

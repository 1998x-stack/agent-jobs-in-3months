"""B04–B06 full offline demonstration: checkpoint -> crash -> lease reclaim -> resume.

Uses a temporary SQLite database, synthetic policy texts and no actual model.
"""
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from agent_harness.scoped_memory import MemoryScope

from .durable_workflow import DurableWorkflow
from .run_repository import RunRepository


def main() -> None:
    question = (
        "refund proposal transfer money human approval "
        "and approved refund processing five business days"
    )
    with TemporaryDirectory() as workdir:
        filename = str(Path(workdir) / "durable.sqlite3")
        repo = RunRepository(filename)
        scope = MemoryScope("demo-tenant", "demo-user")
        run, created = repo.submit(
            scope, idempotency_key="checkpoint-demo-0001",
            question=question, now=100,
        )
        assert created
        first = repo.claim_next(now=101, lease_seconds=5)
        assert first is not None
        first_seen = []

        def crash_after_first_task(step: str) -> None:
            first_seen.append(step)
            if step == "task-01":
                raise KeyboardInterrupt("synthetic hard crash AFTER durable checkpoint")

        try:
            DurableWorkflow(repo, after_checkpoint=crash_after_first_task).execute(
                first, now=102
            )
        except KeyboardInterrupt:
            pass
        else:
            raise AssertionError("expected simulated worker interruption")

        before = repo.checkpoint_keys(first.run.run_id)
        assert before == ("plan", "task-01")
        assert not repo.complete(first, {"status": "stale"}, now=107)
        restarted = RunRepository(filename)
        second = restarted.claim_next(now=108, lease_seconds=10)
        assert second is not None
        report = DurableWorkflow(restarted).execute(second, now=109)
        assert report.reused_steps == ("plan", "task-01")
        assert report.executed_steps == ("task-02",)
        assert restarted.complete(second, report.result, now=110)
        final = restarted.get(scope, run.run_id)
        assert final is not None and final.status == "completed"
        print(json.dumps({
            "crash_after": first_seen,
            "checkpoints_before_restart": before,
            "reused_on_restart": report.reused_steps,
            "executed_on_restart": report.executed_steps,
            "attempts": final.attempt,
            "final_status": final.status,
            "citation_ids": final.result["citation_ids"],
        }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

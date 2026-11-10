"""B04-B06 offline tests: queue contention, lease fencing, retries and checkpoint resume."""
from concurrent.futures import ThreadPoolExecutor
import sqlite3
from threading import Event

import pytest

from agent_harness.scoped_memory import MemoryScope
from agent_runtime.durable_workflow import DurableWorkflow
from agent_runtime.retry_policy import RetryableWorkError, retry_delay
from agent_runtime.run_repository import MAX_ATTEMPTS, RunConflict, RunRepository
from agent_runtime.task_worker import process_one
from agent_runtime.worker_pool import poll_batches, run_batch


@pytest.fixture()
def repo(tmp_path):
    return RunRepository(tmp_path / "durable.sqlite3")


def enqueue(repo, key="durable-run-001", question="refund proposal human approval", now=100):
    return repo.submit(
        MemoryScope("tenant-a", "alice"),
        idempotency_key=key, question=question, now=now,
    )[0]


def test_parallel_worker_batch_processes_each_run_once(repo):
    runs = [
        enqueue(repo, f"run-{index:08d}", "refund proposal human approval")
        for index in range(1, 7)
    ]
    report = run_batch(repo, parallelism=4, max_jobs=10)
    assert len(report.processed_run_ids) == 6
    assert len(set(report.processed_run_ids)) == 6
    assert set(report.processed_run_ids) == {run.run_id for run in runs}
    assert report.idle_slots == 4
    for run in runs:
        final = repo.get(MemoryScope("tenant-a", "alice"), run.run_id)
        assert final.status == "completed"
        assert final.attempt == 1
        assert final.result["checkpoint_count"] == 2
        assert repo.checkpoint_keys(run.run_id) == ("plan", "task-01")
    assert repo.queue_stats()["eligible"] == 0


def test_bounded_idle_polling_uses_stop_event(repo):
    reports = poll_batches(
        repo, Event(), parallelism=2, batch_size=2,
        poll_interval=0.001, max_polls=2,
    )
    assert len(reports) == 2
    assert all(not report.processed_run_ids for report in reports)
    with pytest.raises(ValueError):
        run_batch(repo, parallelism=0)
    with pytest.raises(ValueError):
        poll_batches(repo, Event(), max_polls=0)


def test_retry_backoff_and_attempt_cap(repo):
    item = enqueue(repo)
    first = repo.claim_next(now=101, lease_seconds=20)
    assert first and first.run.attempt == 1
    due = repo.schedule_retry(first, now=102, base_seconds=3, jitter_fraction=0)
    assert due == 105
    assert repo.get(MemoryScope("tenant-a", "alice"), item.run_id).status == "queued"
    assert repo.queue_stats(now=104)["eligible"] == 0
    assert repo.claim_next(now=104) is None
    second = repo.claim_next(now=105, lease_seconds=20)
    assert second and second.run.attempt == 2
    assert repo.schedule_retry(second, now=106, base_seconds=3) == 112
    assert repo.claim_next(now=111) is None
    third = repo.claim_next(now=112, lease_seconds=20)
    assert third and third.run.attempt == MAX_ATTEMPTS
    assert repo.schedule_retry(third, now=113, base_seconds=3) is None
    final = repo.get(MemoryScope("tenant-a", "alice"), item.run_id)
    assert final.status == "failed"
    assert final.error_code == "attempts_exhausted"
    assert repo.claim_next(now=10000) is None


def test_jitter_is_bounded_and_deterministic():
    assert retry_delay(1) == 2.0
    assert retry_delay(2) == 4.0
    assert retry_delay(7, cap_seconds=60) == 60
    one = retry_delay(3, jitter_fraction=0.2, seed="a")
    two = retry_delay(3, jitter_fraction=0.2, seed="a")
    assert 6.4 <= one <= 8 and one == two
    with pytest.raises(ValueError):
        retry_delay(0)
    with pytest.raises(ValueError):
        retry_delay(1, jitter_fraction=1)
    with pytest.raises(ValueError):
        retry_delay(1, cap_seconds=1)


def test_worker_classifies_retryable_failure_and_does_not_leak_error(repo):
    item = enqueue(repo)
    def transient(run):
        raise RetryableWorkError("synthetic SECRET in upstream exception")
    assert process_one(repo, now=101, lease_seconds=20, executor=transient) == item.run_id
    during = repo.get(MemoryScope("tenant-a", "alice"), item.run_id)
    assert during.status == "queued"
    assert during.error_code == "transient_retry"
    assert during.available_at > 101
    assert "SECRET" not in repr(during)
    assert repo.claim_next(now=101) is None
    assert process_one(repo, now=105, lease_seconds=20) == item.run_id
    final = repo.get(MemoryScope("tenant-a", "alice"), item.run_id)
    assert final.status == "completed"
    assert final.attempt == 2
    assert final.result["status"] == "supported"


def test_lease_heartbeat_extends_exclusive_ownership(repo):
    item = enqueue(repo)
    claim = repo.claim_next(now=101, lease_seconds=3)
    assert claim
    renewed = repo.renew_lease(claim, now=102, lease_seconds=12)
    assert renewed and renewed.lease_until == 114
    assert repo.claim_next(now=105) is None
    assert repo.complete(claim, {"status": "ok"}, now=110)
    assert repo.renew_lease(claim, now=111, lease_seconds=5) is None
    assert repo.get(MemoryScope("tenant-a", "alice"), item.run_id).result["status"] == "ok"


def test_expired_worker_cannot_renew_or_write_checkpoint(repo):
    enqueue(repo)
    expired = repo.claim_next(now=101, lease_seconds=2)
    assert expired
    assert repo.renew_lease(expired, now=104) is None
    with pytest.raises(RunConflict, match="stale"):
        repo.save_checkpoint(expired, "plan", {"tasks": []}, now=104)
    with pytest.raises(RunConflict, match="stale"):
        repo.load_checkpoints(expired, now=104)
    fresh = repo.claim_next(now=104, lease_seconds=15)
    assert fresh and fresh.claim_token != expired.claim_token
    with pytest.raises(RunConflict, match="stale"):
        repo.schedule_retry(expired, now=105)
    assert repo.save_checkpoint(fresh, "plan", {"tasks": []}, now=105)


def test_immutable_checkpoint_is_idempotent_and_fenced(repo):
    enqueue(repo)
    claim = repo.claim_next(now=101, lease_seconds=10)
    assert claim
    assert repo.save_checkpoint(claim, "plan", {"tasks": [1]}, now=102)
    assert not repo.save_checkpoint(claim, "plan", {"tasks": [1]}, now=103)
    assert repo.load_checkpoints(claim, now=103) == {"plan": {"tasks": [1]}}
    with pytest.raises(RunConflict, match="immutable"):
        repo.save_checkpoint(claim, "plan", {"tasks": [2]}, now=103)
    with pytest.raises(ValueError):
        repo.save_checkpoint(claim, "../secrets", {"oops": "x"}, now=103)


def test_crash_after_checkpoint_and_resume_without_repeating_task(tmp_path):
    path = tmp_path / "crash.sqlite3"
    original = RunRepository(path)
    actor = MemoryScope("tenant-a", "alice")
    run, _ = original.submit(
        actor, idempotency_key="crash-checkpoint-001",
        question=(
            "refund proposal transfer money human approval "
            "and approved refund processing five business days"
        ),
        now=100,
    )
    first_claim = original.claim_next(now=101, lease_seconds=5)
    assert first_claim
    executed = []
    def hard_crash(step):
        executed.append(step)
        if step == "task-01":
            raise KeyboardInterrupt("simulated kill after COMMIT")
    with pytest.raises(KeyboardInterrupt):
        DurableWorkflow(
            original, after_checkpoint=hard_crash
        ).execute(first_claim, now=102)
    assert executed == ["plan", "task-01"]
    assert original.checkpoint_keys(run.run_id) == ("plan", "task-01")

    # Prove checkpoints survive process/repository reconstruction.
    reopened = RunRepository(path)
    assert reopened.claim_next(now=105) is None
    fresh = reopened.claim_next(now=107, lease_seconds=30)
    assert fresh and fresh.run.attempt == 2
    completed_steps = []
    resumed = DurableWorkflow(
        reopened, after_checkpoint=completed_steps.append
    ).execute(fresh, now=108)
    assert resumed.reused_steps == ("plan", "task-01")
    assert resumed.executed_steps == ("task-02",)
    assert completed_steps == ["task-02"]
    assert resumed.result["status"] == "supported"
    assert len(resumed.result["citation_ids"]) == 2
    assert resumed.result["handoff_count"] == 6
    assert reopened.complete(fresh, resumed.result, now=109)
    assert reopened.get(actor, run.run_id).status == "completed"
    assert not reopened.complete(first_claim, {"status": "stale"}, now=109)
    assert reopened.checkpoint_keys(run.run_id) == ("plan", "task-01", "task-02")


def test_worker_process_one_after_crash_reuses_existing_verified_steps(repo):
    item = enqueue(
        repo, question=(
            "refund proposal transfer money human approval "
            "and approved refund processing five business days"
        )
    )
    def kill(step):
        if step == "task-01":
            raise KeyboardInterrupt("crash")
    with pytest.raises(KeyboardInterrupt):
        process_one(repo, now=101, lease_seconds=2, after_checkpoint=kill)
    assert repo.checkpoint_keys(item.run_id) == ("plan", "task-01")
    assert process_one(repo, now=104, lease_seconds=60) == item.run_id
    assert repo.get(MemoryScope("tenant-a", "alice"), item.run_id).status == "completed"


def test_old_sqlite_schema_migrates_without_data_loss(tmp_path):
    path = tmp_path / "old.sqlite3"
    with sqlite3.connect(path) as db:
        db.execute("""
            CREATE TABLE agent_runs (
                run_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, user_id TEXT NOT NULL,
                request_key TEXT NOT NULL, fingerprint TEXT NOT NULL,
                question TEXT NOT NULL, max_tasks INTEGER NOT NULL,
                max_context_chars INTEGER NOT NULL, status TEXT NOT NULL,
                attempt INTEGER NOT NULL DEFAULT 0, claim_token TEXT,
                lease_until REAL, result_json TEXT, error_code TEXT,
                created_at REAL NOT NULL, updated_at REAL NOT NULL,
                UNIQUE(tenant_id,request_key)
            )
        """)
        db.execute("""
            INSERT INTO agent_runs (
                run_id,tenant_id,user_id,request_key,fingerprint,
                question,max_tasks,max_context_chars,status,created_at,updated_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """, ("old-run", "t", "alice", "k", "old-hash", "refund", 1, 2200, "queued", 1, 1))
    migrated = RunRepository(path)
    assert migrated.get(MemoryScope("t", "alice"), "old-run").question == "refund"
    assert migrated.claim_next(now=10).run.run_id == "old-run"
    assert migrated.checkpoint_keys("old-run") == ()


def test_queue_stats_match_state_transitions(repo):
    enqueue(repo)
    assert repo.queue_stats(now=101)["eligible"] == 1
    claim = repo.claim_next(now=101, lease_seconds=10)
    assert claim
    assert repo.queue_stats(now=102)["running"] == 1
    assert repo.queue_stats(now=102)["eligible"] == 0
    repo.schedule_retry(claim, now=102, base_seconds=5)
    assert repo.queue_stats(now=103)["queued"] == 1
    assert repo.queue_stats(now=103)["eligible"] == 0
    assert repo.queue_stats(now=108)["eligible"] == 1

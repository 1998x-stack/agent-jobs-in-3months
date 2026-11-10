"""B01-B03 contract tests with FastAPI TestClient and no network/API key."""
from concurrent.futures import ThreadPoolExecutor
import json

from fastapi.testclient import TestClient
import pytest

from agent_harness.scoped_memory import MemoryScope
from agent_runtime.run_repository import (
    MAX_ATTEMPTS, RunConflict, RunMissing, RunRepository,
)
from agent_runtime.task_api import create_app
from agent_runtime.task_worker import process_one


TOKENS = {
    "alice-token-this-is-test-00001": MemoryScope("tenant-a", "alice"),
    "bob-token-this-is-test-000002": MemoryScope("tenant-a", "bob"),
    "carol-token-this-is-test-003": MemoryScope("tenant-b", "carol"),
}
BODY = {"question": "refund proposal human approval and refund processing five business days"}


@pytest.fixture()
def api(tmp_path):
    path = str(tmp_path / "agent-runs.sqlite3")
    repository = RunRepository(path)
    app = create_app(path, token_identities=TOKENS)
    with TestClient(app) as client:
        yield client, repository


def headers(token="alice-token-this-is-test-00001", key="request-000001"):
    return {"Authorization": f"Bearer {token}", "Idempotency-Key": key}


def test_submit_get_and_idempotent_replay(api):
    client, repository = api
    first = client.post("/v1/runs", json=BODY, headers=headers())
    assert first.status_code == 202
    assert first.json()["status"] == "queued"
    assert first.json()["attempt"] == 0
    assert first.json()["result"] is None
    replay = client.post("/v1/runs", json=BODY, headers=headers())
    assert replay.status_code == 200
    assert replay.json()["run_id"] == first.json()["run_id"]
    get_result = client.get(
        f"/v1/runs/{first.json()['run_id']}",
        headers={"Authorization": headers()["Authorization"]},
    )
    assert get_result.status_code == 200
    assert get_result.json()["run_id"] == first.json()["run_id"]
    assert repository.claim_next() is not None
    assert repository.claim_next() is None


def test_same_key_with_different_body_or_actor_is_409(api):
    client, _ = api
    assert client.post("/v1/runs", json=BODY, headers=headers()).status_code == 202
    changed = client.post(
        "/v1/runs", json={"question": "shipping dispatch"},
        headers=headers(),
    )
    assert changed.status_code == 409
    actor_changed = client.post(
        "/v1/runs", json=BODY,
        headers=headers(token="bob-token-this-is-test-000002"),
    )
    assert actor_changed.status_code == 409


def test_tenant_keys_are_independent_and_resources_private(api):
    client, _ = api
    a = client.post("/v1/runs", json=BODY, headers=headers()).json()["run_id"]
    b = client.post(
        "/v1/runs", json=BODY,
        headers=headers(token="carol-token-this-is-test-003"),
    ).json()["run_id"]
    assert a != b
    for token in ("bob-token-this-is-test-000002", "carol-token-this-is-test-003"):
        assert client.get(
            f"/v1/runs/{a}",
            headers={"Authorization": f"Bearer {token}"},
        ).status_code == 404
        assert client.post(
            f"/v1/runs/{a}/retry",
            headers={"Authorization": f"Bearer {token}"},
        ).status_code == 404


def test_auth_header_missing_or_bad_is_401(api):
    client, _ = api
    assert client.post("/v1/runs", json=BODY).status_code == 401
    assert client.post(
        "/v1/runs", json=BODY,
        headers={"Authorization": "Bearer wrong-token-this-is-not-configured"},
    ).status_code == 401
    assert client.get("/healthz").json() == {"status": "ok"}


def test_invalid_post_contracts_are_rejected(api):
    client, _ = api
    assert client.post(
        "/v1/runs", json=BODY,
        headers={"Authorization": headers()["Authorization"]},
    ).status_code == 400
    assert client.post(
        "/v1/runs", json=BODY, headers=headers(key="x"),
    ).status_code == 400
    for payload in [
        {"question": ""},
        {"question": " "},
        {"question": "safe", "extra": "unknown"},
        {"question": "safe", "max_tasks": 20},
        {"question": "safe", "max_context_chars": 200},
        {"question": "safe", "max_tasks": "2"},
    ]:
        response = client.post(
            "/v1/runs", json=payload,
            headers=headers(key="validation-0001"),
        )
        assert response.status_code == 422, response.text


def test_worker_executes_real_p1_offline_and_result_is_idempotent(api):
    client, repo = api
    created = client.post("/v1/runs", json=BODY, headers=headers())
    run_id = created.json()["run_id"]
    assert process_one(repo) == run_id
    completed = client.get(
        f"/v1/runs/{run_id}",
        headers={"Authorization": headers()["Authorization"]},
    )
    assert completed.status_code == 200
    result = completed.json()
    assert result["status"] == "completed"
    assert result["attempt"] == 1
    assert result["result"]["status"] == "supported"
    assert len(result["result"]["citation_ids"]) == 2
    assert result["result"]["handoff_count"] == 6
    assert process_one(repo) is None
    replay = client.post("/v1/runs", json=BODY, headers=headers())
    assert replay.json()["run_id"] == run_id
    assert replay.json()["status"] == "completed"
    assert client.post(
        f"/v1/runs/{run_id}/retry",
        headers={"Authorization": headers()["Authorization"]},
    ).status_code == 409


def test_failed_job_retry_and_failed_idempotent_replay(api):
    client, repo = api
    run_id = client.post("/v1/runs", json=BODY, headers=headers()).json()["run_id"]

    def fail_once(run):
        raise RuntimeError("secret value must not be logged")

    assert process_one(repo, executor=fail_once) == run_id
    failed = client.get(
        f"/v1/runs/{run_id}",
        headers={"Authorization": headers()["Authorization"]},
    ).json()
    assert failed["status"] == "failed"
    assert failed["error_code"] == "worker_failed"
    assert "secret value" not in json.dumps(failed)
    same = client.post("/v1/runs", json=BODY, headers=headers())
    assert same.json()["status"] == "failed"
    retry = client.post(
        f"/v1/runs/{run_id}/retry",
        headers={"Authorization": headers()["Authorization"]},
    )
    assert retry.status_code == 202
    assert retry.json()["run_id"] == run_id
    assert retry.json()["status"] == "queued"
    double_retry = client.post(
        f"/v1/runs/{run_id}/retry",
        headers={"Authorization": headers()["Authorization"]},
    )
    assert double_retry.status_code == 202
    assert process_one(repo) == run_id
    done = client.get(
        f"/v1/runs/{run_id}",
        headers={"Authorization": headers()["Authorization"]},
    ).json()
    assert done["status"] == "completed" and done["attempt"] == 2


def test_concurrent_duplicate_submits_are_atomic(tmp_path):
    repo = RunRepository(tmp_path / "race.sqlite3")
    scope = MemoryScope("race-tenant", "alice")

    def submit():
        return repo.submit(
            scope, idempotency_key="race-request-0001",
            question="refund proposal human approval",
        )

    with ThreadPoolExecutor(max_workers=10) as pool:
        results = list(pool.map(lambda _: submit(), range(10)))
    assert len({result.run_id for result, created in results}) == 1
    assert sum(created for _, created in results) == 1
    assert sum(not created for _, created in results) == 9


def test_transaction_conflict_does_not_change_original_record(tmp_path):
    repo = RunRepository(tmp_path / "conflict.sqlite3")
    actor = MemoryScope("tenant-a", "alice")
    first, created = repo.submit(
        actor, idempotency_key="same-key-001", question="refund approval", now=100
    )
    assert created
    with pytest.raises(RunConflict):
        repo.submit(actor, idempotency_key="same-key-001", question="shipping", now=110)
    assert repo.get(actor, first.run_id).question == "refund approval"
    assert repo.get(actor, first.run_id).updated_at == 100.0
    # No open failed transaction remains to block future writes.
    other, created = repo.submit(
        actor, idempotency_key="another-key-001", question="shipping", now=111
    )
    assert created and other.run_id != first.run_id


def test_fencing_rejects_expired_and_reclaimed_workers(tmp_path):
    repo = RunRepository(tmp_path / "fencing.sqlite3")
    actor = MemoryScope("tenant-a", "alice")
    created, _ = repo.submit(
        actor, idempotency_key="fence-req-00001", question="refund approval", now=0
    )
    stale = repo.claim_next(now=1, lease_seconds=5)
    assert stale is not None
    assert repo.claim_next(now=2) is None
    fresh = repo.claim_next(now=7, lease_seconds=10)
    assert fresh is not None
    assert fresh.claim_token != stale.claim_token
    assert fresh.run.attempt == 2
    assert repo.complete(stale, {"status": "bad"}, now=8) is False
    assert repo.complete(fresh, {"status": "ok"}, now=8) is True
    assert repo.get(actor, created.run_id).result == {"status": "ok"}


def test_claim_contention_only_one_worker_claims(tmp_path):
    repo = RunRepository(tmp_path / "worker-race.sqlite3")
    actor = MemoryScope("tenant-a", "alice")
    repo.submit(actor, idempotency_key="worker-req-001", question="refund approval")
    with ThreadPoolExecutor(max_workers=8) as pool:
        claims = list(pool.map(lambda _: repo.claim_next(), range(8)))
    assert sum(claim is not None for claim in claims) == 1


def test_retry_budget_caps_at_three_attempts(tmp_path):
    repo = RunRepository(tmp_path / "retries.sqlite3")
    actor = MemoryScope("tenant-a", "alice")
    run, _ = repo.submit(
        actor, idempotency_key="retry-req-0001", question="refund approval", now=0
    )
    for attempt in range(1, MAX_ATTEMPTS + 1):
        claim = repo.claim_next(now=attempt * 20, lease_seconds=10)
        assert claim and claim.run.attempt == attempt
        assert repo.fail(claim, now=attempt * 20 + 1)
        if attempt < MAX_ATTEMPTS:
            assert repo.retry(actor, run.run_id, now=attempt * 20 + 2).status == "queued"
    with pytest.raises(RunConflict, match="attempt budget"):
        repo.retry(actor, run.run_id, now=100)
    assert repo.claim_next(now=200) is None


def test_retry_cannot_mutate_running_or_invisible_run(tmp_path):
    repo = RunRepository(tmp_path / "state.sqlite3")
    alice = MemoryScope("t", "alice")
    bob = MemoryScope("t", "bob")
    item, _ = repo.submit(
        alice, idempotency_key="running-00001", question="refund approval",
        now=100,
    )
    claim = repo.claim_next(now=101)
    assert claim is not None
    with pytest.raises(RunConflict, match="only failed"):
        repo.retry(alice, item.run_id)
    with pytest.raises(RunMissing):
        repo.retry(bob, item.run_id)
    assert repo.get(bob, item.run_id) is None


def test_final_expired_lease_transitions_to_terminal_failure(tmp_path):
    repo = RunRepository(tmp_path / 'expired-final.sqlite3')
    scope = MemoryScope('tenant-a', 'alice')
    item, _ = repo.submit(scope, idempotency_key='deadline-00001', question='refund approval', now=0)
    for attempt in range(1, MAX_ATTEMPTS + 1):
        claim = repo.claim_next(now=attempt * 10, lease_seconds=5)
        assert claim is not None and claim.run.attempt == attempt
    assert repo.claim_next(now=(MAX_ATTEMPTS + 1) * 10) is None
    final = repo.get(scope, item.run_id)
    assert final.status == 'failed' and final.error_code == 'attempts_exhausted'
    with pytest.raises(RunConflict, match='attempt budget'):
        repo.retry(scope, item.run_id, now=100)

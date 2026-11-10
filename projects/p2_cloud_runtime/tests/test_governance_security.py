"""B07-B10: approval enforcement, RBAC, constrained subprocess and telemetry."""
import hashlib
import io
import json
import subprocess

from fastapi.testclient import TestClient
import pytest

from agent_harness.scoped_memory import MemoryScope
from agent_runtime.approval_gate import ApprovalConflict, ApprovalGate, ApprovalMissing
from agent_runtime.identity import Principal, require_permission
from agent_runtime.observability import (
    SafeEvent, SafeTelemetry, percentile_95, timed_call,
)
from agent_runtime.run_repository import RunRepository
from agent_runtime.sandbox import SandboxPolicy, SandboxRunner, SandboxViolation
from agent_runtime.task_api import create_app
from agent_runtime.task_worker import process_one


TOKENS = {
    "alice-operator-demo-token-123456": Principal(
        MemoryScope("tenant-alpha", "alice"), frozenset({"operator"})
    ),
    "bob-approver-demo-token-1234567": Principal(
        MemoryScope("tenant-alpha", "bob"), frozenset({"approver"})
    ),
    "carol-executor-demo-token-123456": Principal(
        MemoryScope("tenant-alpha", "carol"), frozenset({"executor"})
    ),
    "dave-observer-demo-token-123456": Principal(
        MemoryScope("tenant-alpha", "dave"), frozenset({"observer"})
    ),
    "alice-viewer-demo-token-1234567": Principal(
        MemoryScope("tenant-alpha", "alice"), frozenset({"viewer"})
    ),
    "mallory-cross-tenant-token-12345": Principal(
        MemoryScope("tenant-beta", "mallory"), frozenset({"approver"})
    ),
    "alice-dual-role-test-token-1234": Principal(
        MemoryScope("tenant-alpha", "alice"), frozenset({"operator", "approver"})
    ),
}


def auth(user="alice-operator-demo-token-123456"):
    return {"Authorization": f"Bearer {user}"}


@pytest.fixture()
def context(tmp_path):
    path = str(tmp_path / "governance.sqlite3")
    repo = RunRepository(path)
    telemetry = SafeTelemetry()
    app = create_app(path, token_identities=TOKENS, telemetry=telemetry)
    with TestClient(app) as client:
        yield client, repo, telemetry


def completed_run(client, repository, *, question="refund proposal human approval"):
    headers = {**auth(), "Idempotency-Key": f"test-key-{hashlib.sha256(question.encode()).hexdigest()[:16]}"}
    response = client.post("/v1/runs", headers=headers, json={"question": question})
    assert response.status_code == 202
    run_id = response.json()["run_id"]
    processed = None
    for _ in range(5):
        processed = process_one(repository)
        if processed == run_id:
            break
    assert processed == run_id
    return run_id


def test_four_eyes_approval_full_http_lifecycle(context):
    client, repo, telemetry = context
    run_id = completed_run(client, repo)
    created = client.post(f"/v1/runs/{run_id}/approvals", headers=auth())
    assert created.status_code == 202, created.text
    record = created.json()
    approval_id = record["approval_id"]
    assert record["status"] == "pending" and record["receipt_id"] is None

    replay = client.post(f"/v1/runs/{run_id}/approvals", headers=auth())
    assert replay.status_code == 200
    assert replay.json()["approval_id"] == approval_id
    assert client.post(
        f"/v1/approvals/{approval_id}/execute",
        headers=auth("carol-executor-demo-token-123456")
    ).status_code == 409

    approved = client.post(
        f"/v1/approvals/{approval_id}/decision",
        headers=auth("bob-approver-demo-token-1234567"),
        json={"decision": "approved"},
    )
    assert approved.status_code == 200 and approved.json()["approved_by"] == "bob"
    executed = client.post(
        f"/v1/approvals/{approval_id}/execute",
        headers=auth("carol-executor-demo-token-123456")
    )
    assert executed.status_code == 200 and executed.json()["status"] == "consumed"
    receipt_id = executed.json()["receipt_id"]
    assert receipt_id and len(receipt_id) == 32
    repeated = client.post(
        f"/v1/approvals/{approval_id}/execute",
        headers=auth("carol-executor-demo-token-123456")
    )
    assert repeated.status_code == 200
    assert repeated.json()["receipt_id"] == receipt_id
    assert ApprovalGate(repo).audit_counts(approval_id) == {
        "requested": 1, "approved": 1, "consumed": 1,
    }
    observed = telemetry.summary(operation="approval_execute")
    assert observed["samples"] == 3  # failed preapproval + approved + replay
    assert observed["error_rate"] == round(1 / 3, 4)


def test_rbac_self_approval_and_cross_tenant_denied(context):
    client, repo, _ = context
    run_id = completed_run(client, repo)
    approval_id = client.post(
        f"/v1/runs/{run_id}/approvals", headers=auth(),
    ).json()["approval_id"]
    assert client.post(
        f"/v1/approvals/{approval_id}/decision",
        headers=auth(), json={"decision": "approved"},
    ).status_code == 403
    assert client.post(
        f"/v1/approvals/{approval_id}/decision",
        headers=auth("alice-dual-role-test-token-1234"),
        json={"decision": "approved"},
    ).status_code == 409
    assert client.post(
        f"/v1/approvals/{approval_id}/decision",
        headers=auth("mallory-cross-tenant-token-12345"),
        json={"decision": "approved"},
    ).status_code == 404
    assert client.get(
        f"/v1/approvals/{approval_id}",
        headers=auth("mallory-cross-tenant-token-12345"),
    ).status_code == 404
    assert client.get(
        f"/v1/approvals/{approval_id}",
        headers=auth("alice-viewer-demo-token-1234567"),
    ).status_code == 403
    assert client.post(
        f"/v1/approvals/{approval_id}/execute", headers=auth()
    ).status_code == 403


def test_denied_approval_is_terminal_and_receipt_not_created(context):
    client, repo, _ = context
    run_id = completed_run(client, repo)
    approval_id = client.post(
        f"/v1/runs/{run_id}/approvals", headers=auth()
    ).json()["approval_id"]
    denied = client.post(
        f"/v1/approvals/{approval_id}/decision",
        headers=auth("bob-approver-demo-token-1234567"),
        json={"decision": "denied"},
    )
    assert denied.status_code == 200
    assert denied.json()["status"] == "denied"
    assert client.post(
        f"/v1/approvals/{approval_id}/execute",
        headers=auth("carol-executor-demo-token-123456"),
    ).status_code == 409
    assert client.post(
        f"/v1/approvals/{approval_id}/decision",
        headers=auth("bob-approver-demo-token-1234567"),
        json={"decision": "approved"},
    ).status_code == 409
    assert ApprovalGate(repo).audit_counts(approval_id) == {
        "requested": 1, "denied": 1,
    }


def test_approval_requires_completed_and_supported_run(context):
    client, repo, _ = context
    pending = client.post(
        "/v1/runs",
        headers={**auth(), "Idempotency-Key": "preapproval-00001"},
        json={"question": "refund approval"},
    ).json()["run_id"]
    assert client.post(
        f"/v1/runs/{pending}/approvals", headers=auth()
    ).status_code == 409
    assert client.post(
        "/v1/runs/nonexistent/approvals", headers=auth()
    ).status_code == 404
    unknown = completed_run(client, repo, question="galactic unicorn spaceship")
    assert client.post(
        f"/v1/runs/{unknown}/approvals", headers=auth()
    ).status_code == 409


def test_role_separation_and_legacy_operator_mapping(context, tmp_path):
    client, repo, _ = context
    assert client.post(
        "/v1/runs", headers={**auth("alice-viewer-demo-token-1234567"), "Idempotency-Key": "viewer-request-0001"},
        json={"question": "refund approval"},
    ).status_code == 403
    assert client.post(
        "/v1/runs", headers={**auth("bob-approver-demo-token-1234567"), "Idempotency-Key": "reviewer-request-0001"},
        json={"question": "refund approval"},
    ).status_code == 403
    record = completed_run(client, repo)
    assert client.get(
        f"/v1/runs/{record}", headers=auth("alice-viewer-demo-token-1234567")
    ).status_code == 200
    assert client.get(
        f"/v1/runs/{record}", headers=auth("bob-approver-demo-token-1234567")
    ).status_code == 403
    assert client.get("/v1/observability/summary", headers=auth()).status_code == 403
    assert client.get(
        "/v1/observability/summary",
        headers=auth("dave-observer-demo-token-123456"),
    ).status_code == 200
    with pytest.raises(PermissionError):
        require_permission(TOKENS["alice-viewer-demo-token-1234567"], "runs:submit")
    old = create_app(
        str(tmp_path / "legacy.sqlite3"),
        token_identities={"old-operator-token-123456": MemoryScope("x", "alice")},
    )
    with TestClient(old) as legacy:
        r = legacy.post(
            "/v1/runs",
            headers={
                "Authorization": "Bearer old-operator-token-123456",
                "Idempotency-Key": "legacy-submit-0001",
            },
            json={"question": "refund approval"},
        )
        assert r.status_code == 202


def test_sandbox_allowlisted_hash_and_no_arbitrary_operations(context):
    client, _, _ = context
    good = client.post(
        "/v1/sandbox/hash",
        headers=auth("carol-executor-demo-token-123456"),
        json={"text": "hello world"},
    )
    assert good.status_code == 200, good.text
    assert good.json() == {
        "sha256": hashlib.sha256(b"hello world").hexdigest()
    }
    assert client.post(
        "/v1/sandbox/hash", headers=auth(),
        json={"text": "hello"},
    ).status_code == 403
    assert client.post(
        "/v1/sandbox/hash",
        headers=auth("carol-executor-demo-token-123456"),
        json={"text": "hello", "command": "sh -c rm"},
    ).status_code == 422
    assert client.post(
        "/v1/sandbox/hash",
        headers=auth("carol-executor-demo-token-123456"),
        json={"text": "x" * 600},
    ).status_code == 422
    runner = SandboxRunner()
    assert runner.run("count_words", "red blue green") == {"word_count": 3}
    with pytest.raises(SandboxViolation):
        runner.run("exec_python", "print(1)")
    with pytest.raises(SandboxViolation):
        runner.run("hash_text", "x" * 1000)


def test_sandbox_invocation_has_no_parent_secrets(monkeypatch):
    from agent_runtime import sandbox as module
    captured = {}
    real_run = subprocess.run

    def inspect_run(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        return real_run(*args, **kwargs)

    monkeypatch.setenv("CUSTOM_PARENT_SECRET", "secret-must-not-reach-child")
    monkeypatch.setattr(module.subprocess, "run", inspect_run)
    digest = module.SandboxRunner().run("hash_text", "synthetic")
    assert "sha256" in digest
    assert captured["args"][0][1:3] == ["-I", "-S"]
    assert "CUSTOM_PARENT_SECRET" not in captured["kwargs"]["env"]
    assert captured["kwargs"]["cwd"]
    assert captured["kwargs"]["timeout"] == 2.0
    assert captured["kwargs"]["close_fds"] is True


def test_sandbox_timeout_and_invalid_policy(monkeypatch):
    from agent_runtime import sandbox as module
    def hang(*args, **kwargs):
        raise subprocess.TimeoutExpired("python", 0.1)
    monkeypatch.setattr(module.subprocess, "run", hang)
    with pytest.raises(SandboxViolation, match="timeout"):
        module.SandboxRunner(SandboxPolicy(timeout_seconds=0.1)).run("hash_text", "data")
    with pytest.raises(ValueError):
        module.SandboxPolicy(timeout_seconds=0)


def test_telemetry_p95_slo_denial_and_redaction():
    sink = io.StringIO()
    metrics = SafeTelemetry(sink=sink)
    for number in range(1, 21):
        metrics.record(SafeEvent(
            "http_request",
            "error" if number > 18 else "ok",
            number,
        ))
    summary = metrics.summary(
        operation="http_request",
        target_success_rate=0.90,
        target_p95_ms=19.0,
    )
    assert summary["samples"] == 20
    assert summary["success_rate"] == 0.9
    assert summary["p95_latency_ms"] == 19
    assert summary["slo_status"] == "met"
    assert summary["cost_usd_observed"] is None
    assert metrics.summary(target_success_rate=0.95)["slo_status"] == "breached"
    emitted = sink.getvalue()
    assert "question" not in emitted
    assert "Authorization" not in emitted
    assert "secret" not in emitted
    for line in emitted.splitlines():
        assert set(json.loads(line)) == {
            "operation", "outcome", "duration_ms", "attempt", "cost_usd",
        }
    with pytest.raises(ValueError):
        SafeEvent("raw_user_prompt", "ok", 1)
    with pytest.raises(ValueError):
        SafeEvent("http_request", "ok", float("nan"))


def test_telemetry_small_samples_and_rolling_window():
    metrics = SafeTelemetry(max_events=2)
    assert metrics.summary()["slo_status"] == "insufficient_samples"
    metrics.record(SafeEvent("worker_run", "error", 10, attempt=1))
    metrics.record(SafeEvent("worker_run", "ok", 20, attempt=2))
    metrics.record(SafeEvent("worker_run", "ok", 30, attempt=3))
    assert metrics.summary(operation="worker_run", min_samples=2)["samples"] == 2
    assert metrics.summary(operation="worker_run", min_samples=2)["p95_latency_ms"] == 30
    assert percentile_95([]) is None
    assert percentile_95([1, 10, 20]) == 20


def test_worker_instrumentation_never_logs_exception_text(context):
    _, repo, _ = context
    scope = MemoryScope("tenant-alpha", "alice")
    run, _ = repo.submit(
        scope, idempotency_key="telemetry-worker-run-001",
        question="refund approval",
    )
    sink = io.StringIO()
    metrics = SafeTelemetry(sink=sink)

    def failing_executor(job):
        raise RuntimeError("THIS-SECRET-SHOULD-NOT-APPEAR")

    assert process_one(repo, executor=failing_executor, telemetry=metrics) == run.run_id
    summary = metrics.summary(operation="worker_run", min_samples=1)
    assert summary["samples"] == 1 and summary["error_rate"] == 1
    assert "THIS-SECRET" not in sink.getvalue()
    assert "refund" not in sink.getvalue()
    assert repo.get(scope, run.run_id).status == "failed"


def test_timed_call_marks_denials_without_recording_arguments():
    metrics = SafeTelemetry()
    def deny():
        raise PermissionError("private secret error text")
    with pytest.raises(PermissionError):
        timed_call("sandbox_hash", metrics, deny)
    assert metrics.summary(operation="sandbox_hash", min_samples=1)["error_rate"] == 1
    assert metrics._events[0].outcome == "denied"

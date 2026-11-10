"""B07-B10 offline integration: human approval, RBAC, subprocess, safe metrics.

This is a SYNTHETIC receipt, not a refund or external side effect.
No live model, network server or persistent credential is used.
"""
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi.testclient import TestClient

from agent_harness.scoped_memory import MemoryScope

from .approval_gate import ApprovalGate
from .identity import Principal
from .run_repository import RunRepository
from .task_api import create_app
from .task_worker import process_one


def main() -> None:
    tokens = {
        "demo-operator-token-000001": Principal(
            MemoryScope("synthetic", "requester"), frozenset({"operator"})
        ),
        "demo-approver-token-000002": Principal(
            MemoryScope("synthetic", "reviewer"), frozenset({"approver"})
        ),
        "demo-executor-token-000003": Principal(
            MemoryScope("synthetic", "executor"), frozenset({"executor"})
        ),
        "demo-observer-token-000004": Principal(
            MemoryScope("synthetic", "auditor"), frozenset({"observer"})
        ),
    }
    def headers(role):
        return {"Authorization": f"Bearer demo-{role}-token-" + {
            "operator": "000001", "approver": "000002",
            "executor": "000003", "observer": "000004",
        }[role]}

    with TemporaryDirectory() as workdir:
        filename = str(Path(workdir) / "policy-governance.sqlite3")
        repository = RunRepository(filename)
        app = create_app(filename, token_identities=tokens)
        with TestClient(app) as client:
            response = client.post(
                "/v1/runs",
                headers={**headers("operator"), "Idempotency-Key": "governance-demo-0001"},
                json={"question": "refund proposal transfer money human approval"},
            )
            response.raise_for_status()
            run_id = response.json()["run_id"]
            assert process_one(repository) == run_id
            created = client.post(
                f"/v1/runs/{run_id}/approvals", headers=headers("operator")
            )
            created.raise_for_status()
            approval_id = created.json()["approval_id"]
            before = client.post(
                f"/v1/approvals/{approval_id}/execute", headers=headers("executor")
            )
            assert before.status_code == 409
            human = client.post(
                f"/v1/approvals/{approval_id}/decision",
                headers=headers("approver"), json={"decision": "approved"},
            )
            human.raise_for_status()
            consumed = client.post(
                f"/v1/approvals/{approval_id}/execute", headers=headers("executor")
            )
            consumed.raise_for_status()
            second = client.post(
                f"/v1/approvals/{approval_id}/execute", headers=headers("executor")
            )
            assert second.json()["receipt_id"] == consumed.json()["receipt_id"]
            hashed = client.post(
                "/v1/sandbox/hash",
                headers=headers("executor"), json={"text": "synthetic receipt"},
            )
            hashed.raise_for_status()
            status = client.get(
                "/v1/observability/summary", headers=headers("observer")
            )
            status.raise_for_status()
            print(json.dumps({
                "task_status": "completed",
                "unapproved_execution_http": before.status_code,
                "approval_status": consumed.json()["status"],
                "receipt_replay_is_same": (
                    second.json()["receipt_id"] == consumed.json()["receipt_id"]
                ),
                "audit_counts": ApprovalGate(repository).audit_counts(approval_id),
                "sandbox_hash_ok": len(hashed.json()["sha256"]) == 64,
                "telemetry_samples": status.json()["samples"],
                "slo_status": status.json()["slo_status"],
            }, indent=2))


if __name__ == "__main__":
    main()

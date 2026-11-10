"""Fully in-process HTTP flow: submit -> execute offline P1 -> query -> replay.

Runs without a listening server, API key, network calls or paid LLM.
"""
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi.testclient import TestClient
from agent_harness.scoped_memory import MemoryScope

from .run_repository import RunRepository
from .task_api import create_app
from .task_worker import process_one


def main() -> None:
    with TemporaryDirectory() as workdir:
        path = str(Path(workdir) / "runs.sqlite3")
        token = "offline-demo-test-token-12345678"
        app = create_app(
            path, token_identities={token: MemoryScope("tenant-demo", "alice")},
        )
        headers = {
            "Authorization": f"Bearer {token}",
            "Idempotency-Key": "run-demo-000001",
        }
        payload = {
            "question": (
                "refund proposal transfer money human approval "
                "and approved refund processing five business days"
            )
        }
        with TestClient(app) as client:
            first = client.post("/v1/runs", headers=headers, json=payload)
            first.raise_for_status()
            run_id = first.json()["run_id"]
            repeated = client.post("/v1/runs", headers=headers, json=payload)
            repeated.raise_for_status()
            assert repeated.json()["run_id"] == run_id
            assert repeated.status_code == 200
            before = client.get(
                f"/v1/runs/{run_id}", headers={"Authorization": f"Bearer {token}"}
            )
            assert before.json()["status"] == "queued"
            process_one(RunRepository(path))
            after = client.get(
                f"/v1/runs/{run_id}", headers={"Authorization": f"Bearer {token}"}
            )
            after.raise_for_status()
            print(json.dumps({
                "created_status": first.status_code,
                "replay_status": repeated.status_code,
                "same_run_id": repeated.json()["run_id"] == run_id,
                "final_status": after.json()["status"],
                "verified_citations": after.json()["result"]["citation_ids"],
            }, indent=2))


if __name__ == "__main__":
    main()

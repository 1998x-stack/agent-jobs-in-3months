"""Run: PYTHONPATH=projects/p2_cloud_runtime/src python -m agent_runtime.demo"""
from .approval import ApprovalLedger
from .storage import TaskStore

def main() -> None:
    store = TaskStore()
    job_id = store.submit("demo-request", {"task": "draft refund proposal"})
    claim = store.claim(now=100.0)
    assert claim is not None
    assert store.complete(job_id, claim["token"], "proposal ready", now=101.0)
    approvals = ApprovalLedger()
    print("Job:", store.get(job_id)["status"])
    print("First approval:", approvals.approve_once("refund-demo", "reviewer", 2500))
    print("Repeated approval:", approvals.approve_once("refund-demo", "reviewer", 2500))

if __name__ == "__main__":
    main()

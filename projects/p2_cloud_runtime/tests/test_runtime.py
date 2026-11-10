from agent_runtime.approval import ApprovalLedger
from agent_runtime.security import authorize
from agent_runtime.storage import TaskStore
from agent_runtime.workflow import validate_transition
import pytest

def test_submit_idempotency():
    store = TaskStore()
    one = store.submit("k", {"x": 1})
    two = store.submit("k", {"x": 1})
    assert one == two

def test_expired_lease_and_fencing_token():
    store = TaskStore()
    job_id = store.submit("k", {"goal": "demo"})
    old = store.claim(now=0.0, lease_seconds=5)
    assert old is not None
    assert store.claim(now=1.0) is None
    new = store.claim(now=6.0, lease_seconds=5)
    assert new and new["attempt"] == 2
    assert not store.complete(job_id, old["token"], "stale", now=7.0)
    assert store.complete(job_id, new["token"], "good", now=7.0)

def test_duplicate_approval_only_recorded_once():
    ledger = ApprovalLedger()
    assert ledger.approve_once("refund:1", "human", 1000)
    assert not ledger.approve_once("refund:1", "human", 1000)
    assert ledger.count() == 1

def test_tenant_and_state_boundaries():
    with pytest.raises(PermissionError):
        authorize("a", "b")
    with pytest.raises(ValueError):
        validate_transition("completed", "running")

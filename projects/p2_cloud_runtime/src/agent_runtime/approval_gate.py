"""B07: durable, audited four-eyes human approval for a SYNTHETIC receipt.

No financial/external effect is performed. request -> approved/denied ->
consume is enforced within SQLite transactions. Approval state is scoped by
tenant and a completed, actor-owned P1 Agent run; the approver and executor
must be distinct from both the requester and each other.
"""
from dataclasses import dataclass
import json
import sqlite3
import time
import uuid

from .identity import Principal, authorize_tenant, require_permission
from .run_repository import RunConflict, RunRepository


class ApprovalConflict(ValueError):
    """Denied, invalid, or completed approval state."""


class ApprovalMissing(LookupError):
    """Approval is not visible to this principal."""


@dataclass(frozen=True)
class ApprovalRecord:
    approval_id: str
    run_id: str
    action: str
    status: str
    requested_by: str
    approved_by: str | None
    receipt_id: str | None


class ApprovalGate:
    """Only one allowed synthetic action, with audit events and atomic consume."""

    ACTION = "release_demo_receipt"

    def __init__(self, repository: RunRepository) -> None:
        self.repository = repository
        with self.repository._write() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS approvals_v2 (
                    approval_id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    run_id TEXT NOT NULL REFERENCES agent_runs(run_id),
                    requested_by TEXT NOT NULL,
                    action TEXT NOT NULL,
                    status TEXT NOT NULL
                      CHECK(status IN ('pending','approved','denied','consumed')),
                    approved_by TEXT,
                    created_at REAL NOT NULL,
                    decided_at REAL,
                    consumed_at REAL,
                    UNIQUE(tenant_id, run_id, action)
                )
            """)
            db.execute("""
                CREATE TABLE IF NOT EXISTS approval_receipts (
                    approval_id TEXT PRIMARY KEY
                      REFERENCES approvals_v2(approval_id),
                    receipt_id TEXT UNIQUE NOT NULL
                )
            """)
            db.execute("""
                CREATE TABLE IF NOT EXISTS approval_audit (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    approval_id TEXT NOT NULL REFERENCES approvals_v2(approval_id),
                    actor_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    timestamp REAL NOT NULL
                )
            """)

    @staticmethod
    def _record(db: sqlite3.Connection, row: sqlite3.Row) -> ApprovalRecord:
        receipt = db.execute("""
            SELECT receipt_id FROM approval_receipts WHERE approval_id=?
        """, (row["approval_id"],)).fetchone()
        return ApprovalRecord(
            approval_id=row["approval_id"], run_id=row["run_id"],
            action=row["action"], status=row["status"],
            requested_by=row["requested_by"],
            approved_by=row["approved_by"],
            receipt_id=receipt["receipt_id"] if receipt else None,
        )

    @staticmethod
    def _event(
        db: sqlite3.Connection,
        approval_id: str,
        actor_id: str,
        event_type: str,
        stamp: float,
    ) -> None:
        db.execute("""
            INSERT INTO approval_audit(approval_id, actor_id, event_type, timestamp)
            VALUES (?, ?, ?, ?)
        """, (approval_id, actor_id, event_type, stamp))

    def request(
        self, principal: Principal, run_id: str, *,
        action: str = ACTION, now: float | None = None,
    ) -> tuple[ApprovalRecord, bool]:
        require_permission(principal, "approvals:request")
        if action != self.ACTION:
            raise ApprovalConflict("only an allowlisted synthetic receipt can be requested")
        if not isinstance(run_id, str) or not run_id:
            raise ValueError("run id required")
        stamp = time.time() if now is None else float(now)
        scope = principal.scope
        with self.repository._write() as db:
            run = db.execute("""
                SELECT status, result_json FROM agent_runs
                WHERE run_id=? AND tenant_id=? AND user_id=?
            """, (run_id, scope.tenant_id, scope.user_id)).fetchone()
            if not run:
                raise ApprovalMissing("run not found")
            if run["status"] != "completed":
                raise ApprovalConflict("run must be completed before approval can be requested")
            if not run["result_json"] or json.loads(run["result_json"]).get("status") != "supported":
                raise ApprovalConflict("a supported, verified result is required")
            existing = db.execute("""
                SELECT * FROM approvals_v2
                WHERE tenant_id=? AND run_id=? AND action=?
            """, (scope.tenant_id, run_id, action)).fetchone()
            if existing:
                return self._record(db, existing), False
            approval_id = uuid.uuid4().hex
            db.execute("""
                INSERT INTO approvals_v2 (
                    approval_id, tenant_id, run_id, requested_by,
                    action, status, created_at
                ) VALUES (?, ?, ?, ?, ?, 'pending', ?)
            """, (approval_id, scope.tenant_id, run_id, scope.user_id, action, stamp))
            self._event(db, approval_id, scope.user_id, "requested", stamp)
            row = db.execute(
                "SELECT * FROM approvals_v2 WHERE approval_id=?", (approval_id,)
            ).fetchone()
            return self._record(db, row), True

    def get(self, principal: Principal, approval_id: str) -> ApprovalRecord:
        if not any(principal.allows(perm) for perm in (
            "approvals:read", "approvals:request"
        )):
            raise PermissionError("permission denied")
        with self.repository._connect() as db:
            row = db.execute("""
                SELECT * FROM approvals_v2
                WHERE approval_id=? AND tenant_id=?
            """, (approval_id, principal.scope.tenant_id)).fetchone()
            if row is None:
                raise ApprovalMissing("approval not found")
            if not principal.allows("approvals:read") and row["requested_by"] != principal.scope.user_id:
                raise ApprovalMissing("approval not found")
            return self._record(db, row)

    def decide(
        self, principal: Principal, approval_id: str,
        *, decision: str, now: float | None = None,
    ) -> ApprovalRecord:
        require_permission(principal, "approvals:decide")
        if decision not in ("approved", "denied"):
            raise ValueError("decision must be approved or denied")
        stamp = time.time() if now is None else float(now)
        with self.repository._write() as db:
            row = db.execute("""
                SELECT * FROM approvals_v2
                WHERE approval_id=? AND tenant_id=?
            """, (approval_id, principal.scope.tenant_id)).fetchone()
            if row is None:
                raise ApprovalMissing("approval not found")
            if row["requested_by"] == principal.scope.user_id:
                raise ApprovalConflict("requester cannot self-approve")
            if row["status"] != "pending":
                raise ApprovalConflict("approval is no longer pending")
            db.execute("""
                UPDATE approvals_v2
                SET status=?, approved_by=?, decided_at=?
                WHERE approval_id=? AND status='pending'
            """, (decision, principal.scope.user_id, stamp, approval_id))
            self._event(db, approval_id, principal.scope.user_id, decision, stamp)
            updated = db.execute(
                "SELECT * FROM approvals_v2 WHERE approval_id=?", (approval_id,)
            ).fetchone()
            return self._record(db, updated)

    def execute(
        self, principal: Principal, approval_id: str,
        *, now: float | None = None,
    ) -> ApprovalRecord:
        """Atomically consume approval and record a synthetic receipt once."""
        require_permission(principal, "approvals:execute")
        stamp = time.time() if now is None else float(now)
        with self.repository._write() as db:
            row = db.execute("""
                SELECT * FROM approvals_v2
                WHERE approval_id=? AND tenant_id=?
            """, (approval_id, principal.scope.tenant_id)).fetchone()
            if row is None:
                raise ApprovalMissing("approval not found")
            if principal.scope.user_id in (row["requested_by"], row["approved_by"]):
                raise ApprovalConflict("executor must be independent of requester and approver")
            if row["status"] == "consumed":
                return self._record(db, row)  # deterministic exact replay
            if row["status"] != "approved":
                raise ApprovalConflict("human approval required before execute")
            if row["action"] != self.ACTION:
                raise ApprovalConflict("operation is not allowlisted")
            receipt_id = uuid.uuid4().hex
            db.execute("""
                INSERT INTO approval_receipts(approval_id, receipt_id)
                VALUES (?, ?)
            """, (approval_id, receipt_id))
            db.execute("""
                UPDATE approvals_v2 SET status='consumed', consumed_at=?
                WHERE approval_id=? AND status='approved'
            """, (stamp, approval_id))
            self._event(db, approval_id, principal.scope.user_id, "consumed", stamp)
            updated = db.execute(
                "SELECT * FROM approvals_v2 WHERE approval_id=?", (approval_id,)
            ).fetchone()
            return self._record(db, updated)

    def audit_counts(self, approval_id: str) -> dict[str, int]:
        """Only for trusted offline diagnostics; not exposed as an HTTP route."""
        with self.repository._connect() as db:
            rows = db.execute("""
                SELECT event_type, COUNT(*) AS n FROM approval_audit
                WHERE approval_id=? GROUP BY event_type
            """, (approval_id,)).fetchall()
            return {row["event_type"]: int(row["n"]) for row in rows}

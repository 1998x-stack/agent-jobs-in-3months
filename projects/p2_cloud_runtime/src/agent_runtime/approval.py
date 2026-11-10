"""Demonstration-only approval ledger with unique operation keys."""
import sqlite3

class ApprovalLedger:
    def __init__(self) -> None:
        self.conn = sqlite3.connect(":memory:")
        self.conn.execute("""
            CREATE TABLE approvals (
                operation_key TEXT PRIMARY KEY,
                approved_by TEXT NOT NULL,
                amount_cents INTEGER NOT NULL
            )
        """)

    def approve_once(self, operation_key: str, approved_by: str,
                     amount_cents: int) -> bool:
        if not operation_key or not approved_by or amount_cents < 0:
            raise ValueError("invalid approval")
        result = self.conn.execute("""
            INSERT OR IGNORE INTO approvals
            (operation_key, approved_by, amount_cents) VALUES (?, ?, ?)
        """, (operation_key, approved_by, amount_cents))
        self.conn.commit()
        return result.rowcount == 1

    def count(self) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM approvals").fetchone()[0]

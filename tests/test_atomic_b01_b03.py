"""Self-check all B01-B03 atomic coding exercises."""
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("unit", [
    "b01_backend_async", "b02_database_transactions", "b03_idempotency",
])
def test_self_check(unit: str) -> None:
    path = ROOT / "curriculum" / "s2_production_systems" / unit / "check_exercise.py"
    run = subprocess.run(
        [sys.executable, str(path)],
        capture_output=True, text=True, cwd=ROOT, timeout=20, check=False,
    )
    assert run.returncode == 0, run.stdout + run.stderr
    assert "PASS" in run.stdout

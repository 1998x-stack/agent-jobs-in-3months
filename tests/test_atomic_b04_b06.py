"""B04-B06 standalone teaching exercises, checked offline through pytest."""
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("unit", [
    "b04_queue_workers", "b05_leases_retries", "b06_durable_execution",
])
def test_atomic_skill(unit: str) -> None:
    path = ROOT / "curriculum" / "s2_production_systems" / unit / "check_exercise.py"
    result = subprocess.run(
        [sys.executable, str(path)], cwd=ROOT, timeout=20,
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASS" in result.stdout

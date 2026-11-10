"""C01–C03 independent exercises and offline self-checks."""
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("slug", [
    "c01_task_datasets", "c02_gold_state", "c03_trajectory_eval",
])
def test_skill(slug: str) -> None:
    path = ROOT / "curriculum" / "s3_evaluation_learning" / slug / "check_exercise.py"
    result = subprocess.run(
        [sys.executable, str(path)],
        cwd=ROOT, capture_output=True, text=True, timeout=15, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASS" in result.stdout

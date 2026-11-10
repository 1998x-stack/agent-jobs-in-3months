"""C04–C06 runnable standalone exercises with dedicated assertions."""
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("skill", [
    "c04_safety_eval", "c05_statistics", "c06_ablation",
])
def test_atomic_skill(skill: str) -> None:
    program = ROOT / "curriculum" / "s3_evaluation_learning" / skill / "check_exercise.py"
    finished = subprocess.run(
        [sys.executable, str(program)],
        cwd=ROOT, capture_output=True, text=True, timeout=20, check=False,
    )
    assert finished.returncode == 0, finished.stdout + finished.stderr
    assert "PASS" in finished.stdout

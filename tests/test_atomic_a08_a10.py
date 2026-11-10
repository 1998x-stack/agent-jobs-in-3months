"""A08-A10 standalone exercise checks, no network or model token needed."""
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("slug", [
    "a08_context_engineering", "a09_memory_state",
    "a10_planning_multi_agent",
])
def test_skill_check(slug: str) -> None:
    path = ROOT / "curriculum" / "s1_agent_architecture" / slug / "check_exercise.py"
    run = subprocess.run(
        [sys.executable, str(path)],
        capture_output=True, text=True, cwd=ROOT, timeout=10, check=False,
    )
    assert run.returncode == 0, run.stdout + run.stderr
    assert "PASS" in run.stdout

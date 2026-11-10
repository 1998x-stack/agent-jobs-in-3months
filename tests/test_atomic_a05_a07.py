"""Standalone A05-A07 smoke tests: no API key required."""
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("name", [
    "a05_tool_design", "a06_retrieval_rag", "a07_grounding",
])
def test_atomic_skill_self_check(name: str) -> None:
    program = ROOT / "curriculum" / "s1_agent_architecture" / name / "check_exercise.py"
    result = subprocess.run(
        [sys.executable, str(program)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASS" in result.stdout

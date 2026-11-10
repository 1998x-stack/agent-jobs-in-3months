"""Exercise verification, run through pytest without any API key."""
from pathlib import Path
import subprocess
import sys
import pytest

ROOT = Path(__file__).resolve().parents[1]

@pytest.mark.parametrize("name", [
    "a01_llm_api_tokens", "a02_structured_output",
    "a03_tool_calling", "a04_agent_loop",
])
def test_completed_skill_checks(name):
    path = ROOT / "curriculum" / "s1_agent_architecture" / name / "check_exercise.py"
    result = subprocess.run(
        [sys.executable, str(path)],
        cwd=ROOT, capture_output=True, text=True, timeout=10, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASS" in result.stdout

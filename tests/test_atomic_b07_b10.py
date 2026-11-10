"""B07-B10 standalone coding challenges, validated without a model or network."""
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("slug", [
    "b07_human_approval", "b08_identity_authorization",
    "b09_sandbox", "b10_observability_slo",
])
def test_unit(slug: str) -> None:
    program = ROOT / "curriculum" / "s2_production_systems" / slug / "check_exercise.py"
    result = subprocess.run(
        [sys.executable, str(program)],
        cwd=ROOT, text=True, capture_output=True, timeout=20, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASS" in result.stdout

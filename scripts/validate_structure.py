"""Lightweight stdlib-only scaffold validation, without pytest installed."""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
dirs = sorted((root / "curriculum").glob("s[123]_*/*"))
skills = [d for d in dirs if d.is_dir()]
assert len(skills) == 30, f"expected 30 skills, found {len(skills)}"
for path in skills:
    for file in ("README.md", "concept.md", "exercise.py", "check_exercise.py"):
        assert (path / file).exists(), f"missing {path / file}"
for number in range(1, 13):
    assert (root / "weeks" / f"w{number:02d}" / "README.md").exists()
print("Scaffold OK: 30 skills, 12 weeks")

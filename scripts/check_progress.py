"""Print completed atomic skills by scanning for unfinished exercise markers."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
exercises = sorted((ROOT / "curriculum").glob("s[123]_*/*/exercise.py"))
incomplete = []
for path in exercises:
    source = path.read_text(encoding="utf-8")
    if "raise NotImplementedError(" in source:
        incomplete.append(path)
done = len(exercises) - len(incomplete)
print(f"Atomic skills: {done}/{len(exercises)} exercises no longer use TODO stubs")
for path in incomplete[:8]:
    print("  TODO", path.relative_to(ROOT))
if len(incomplete) > 8:
    print(f"  ... and {len(incomplete) - 8} more")
print("Note: removing a stub is not proof of mastery; run tests and capture evidence.")

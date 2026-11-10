"""Dataset loader with minimal validation; versioned dataset schemas are TODO."""
import json
from pathlib import Path

def load_cases(path: str | Path) -> list[dict]:
    cases = []
    with Path(path).open(encoding="utf-8") as stream:
        for lineno, line in enumerate(stream, start=1):
            if not line.strip():
                continue
            case = json.loads(line)
            required = {"id", "expected_outcome", "required_tools"}
            if not required.issubset(case):
                raise ValueError(f"invalid case at line {lineno}")
            cases.append(case)
    return cases

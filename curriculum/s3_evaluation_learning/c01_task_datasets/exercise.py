"""C01: build validated scenario-tagged train/dev/holdout JSONL records."""
import hashlib
import json
from typing import Any


def solve(input_data: dict[str, Any]) -> dict[str, Any]:
    rows = input_data.get("cases")
    if not isinstance(rows, list) or not rows:
        raise ValueError("nonempty cases required")
    seen: set[str] = set()
    groups: dict[str, str] = {}
    normalized: list[dict] = []
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"id", "split", "group_id", "question", "tags"}:
            raise ValueError("case requires exactly id, split, group_id, question, tags")
        case_id, split, group = row["id"], row["split"], row["group_id"]
        if not all(isinstance(x, str) and x.strip() for x in (case_id, split, group, row["question"])):
            raise ValueError("invalid or blank identity/question")
        if split not in ("train", "dev", "holdout"):
            raise ValueError("unknown split")
        if case_id in seen:
            raise ValueError("duplicate case ID")
        seen.add(case_id)
        if group in groups and groups[group] != split:
            raise ValueError("leakage across dataset splits")
        groups[group] = split
        tags = row["tags"]
        if not isinstance(tags, list) or not tags or any(
            not isinstance(tag, str) or not tag.strip() for tag in tags
        ):
            raise ValueError("nonempty tags required")
        normalized.append(row)
    lines = "\n".join(json.dumps(row, sort_keys=True) for row in normalized)
    return {
        "count": len(normalized),
        "jsonl": lines,
        "sha256": hashlib.sha256(lines.encode()).hexdigest(),
        "splits": {s: sum(r["split"] == s for r in normalized) for s in ("train", "dev", "holdout")},
    }

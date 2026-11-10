"""C05: paired success delta + seeded 95% percentile bootstrap, stdlib only."""
import random
from typing import Any


def solve(input_data: dict[str, Any]) -> dict[str, Any]:
    rows = input_data.get("pairs")
    samples = input_data.get("samples", 1000)
    seed = input_data.get("seed", 7)
    if not isinstance(rows, list) or not rows:
        raise ValueError("nonempty case pairs required")
    if type(samples) is not int or not 1 <= samples <= 20000:
        raise ValueError("samples must be 1..20000")
    if type(seed) is not int:
        raise ValueError("seed must be integer")
    pairs: dict[str, tuple[bool, bool]] = {}
    for item in rows:
        if not isinstance(item, dict) or set(item) != {
            "case_id", "control", "variant"
        }:
            raise ValueError("exact case_id, control, variant required")
        if not isinstance(item["case_id"], str) or not item["case_id"]:
            raise ValueError("case ID required")
        if item["case_id"] in pairs:
            raise ValueError("duplicate case ID")
        if type(item["control"]) is not bool or type(item["variant"]) is not bool:
            raise ValueError("paired outcomes must be booleans")
        pairs[item["case_id"]] = (item["control"], item["variant"])
    differences = [
        int(variant) - int(control)
        for control, variant in (pairs[key] for key in sorted(pairs))
    ]
    n = len(differences)
    rng = random.Random(seed)
    boots = sorted(
        sum(differences[rng.randrange(n)] for _ in range(n)) / n
        for _ in range(samples)
    )
    return {
        "n": n,
        "delta": sum(differences) / n,
        "bootstrap_ci_95": [
            boots[int((samples - 1) * 0.025)],
            boots[int((samples - 1) * 0.975)],
        ],
        "wins": differences.count(1),
        "losses": differences.count(-1),
        "small_sample": n < 30,
    }

"""B10: compute p95, error rate and sample-qualified SLO from safe metadata."""
import math
from typing import Any


def solve(input_data: dict[str, Any]) -> dict[str, Any]:
    samples = input_data.get("samples")
    threshold = input_data.get("p95_target_ms", 100)
    success_target = input_data.get("success_target", 0.99)
    min_samples = input_data.get("min_samples", 5)
    if not isinstance(samples, list) or not samples:
        raise ValueError("nonempty sample list required")
    if not 0 < threshold or not 0 < success_target <= 1 or type(min_samples) is not int or min_samples < 1:
        raise ValueError("invalid SLO thresholds")
    durations = []
    successes = 0
    for sample in samples:
        if not isinstance(sample, dict) or set(sample) != {"duration_ms", "ok"}:
            raise ValueError("only safe duration and status metadata allowed")
        duration = sample["duration_ms"]
        if not isinstance(duration, (int, float)) or not math.isfinite(duration) or duration < 0:
            raise ValueError("invalid latency")
        if type(sample["ok"]) is not bool:
            raise ValueError("status must be boolean")
        durations.append(duration)
        successes += sample["ok"]
    durations.sort()
    p95 = durations[math.ceil(0.95 * len(durations)) - 1]
    success_rate = successes / len(durations)
    status = (
        "insufficient_samples" if len(samples) < min_samples
        else "met" if p95 <= threshold and success_rate >= success_target
        else "breached"
    )
    return {
        "count": len(samples), "p95_latency_ms": p95,
        "success_rate": round(success_rate, 4), "slo_status": status,
    }

"""Paired bootstrap for success-rate delta; demonstration, not causal proof."""
import random

def paired_delta_ci(base: list[bool], variant: list[bool],
                    samples: int = 2000, seed: int = 7) -> tuple[float, float, float]:
    if len(base) != len(variant) or not base:
        raise ValueError("paired nonempty equal-length inputs required")
    if samples < 1:
        raise ValueError("samples must be positive")
    differences = [int(v) - int(b) for b, v in zip(base, variant)]
    n = len(differences)
    observed = sum(differences) / n
    rng = random.Random(seed)
    draws = sorted(
        sum(differences[rng.randrange(n)] for _ in range(n)) / n
        for _ in range(samples)
    )
    lo = draws[int((samples - 1) * 0.025)]
    hi = draws[int((samples - 1) * 0.975)]
    return observed, lo, hi

"""C05: paired success-rate statistics aligned by stable case ID.

The unit of resampling is a case pair, not individual unpaired requests.
Bootstrap percentile intervals and exact discordance p-values are descriptive;
small synthetic fixture experiments do not prove a causal model improvement.
"""
from dataclasses import dataclass
from math import comb
from typing import Mapping

from .statistics import paired_delta_ci


@dataclass(frozen=True)
class PairedReport:
    n: int
    control_successes: int
    variant_successes: int
    control_rate: float
    variant_rate: float
    delta: float
    bootstrap_ci_95: tuple[float, float]
    wins: int
    losses: int
    ties: int
    mcnemar_exact_p: float
    evidence_status: str
    bootstrap_samples: int
    seed: int

    def as_dict(self) -> dict:
        return {
            "n": self.n,
            "control_successes": self.control_successes,
            "variant_successes": self.variant_successes,
            "control_rate": self.control_rate,
            "variant_rate": self.variant_rate,
            "delta": self.delta,
            "bootstrap_ci_95": list(self.bootstrap_ci_95),
            "wins": self.wins,
            "losses": self.losses,
            "ties": self.ties,
            "discordant_pairs": self.wins + self.losses,
            "mcnemar_exact_p": self.mcnemar_exact_p,
            "evidence_status": self.evidence_status,
            "bootstrap_samples": self.bootstrap_samples,
            "seed": self.seed,
        }


def exact_discordance_p(wins: int, losses: int) -> float:
    """Exact two-sided binomial/McNemar p-value on discordant paired cases."""
    if type(wins) is not int or type(losses) is not int or min(wins, losses) < 0:
        raise ValueError("wins and losses must be nonnegative integers")
    discordant = wins + losses
    if discordant == 0:
        return 1.0
    smaller = min(wins, losses)
    tail = sum(comb(discordant, k) for k in range(smaller + 1)) / (2 ** discordant)
    return min(1.0, 2.0 * tail)


def compare_paired_by_id(
    control: Mapping[str, bool],
    variant: Mapping[str, bool],
    *,
    bootstrap_samples: int = 2000,
    seed: int = 7,
    min_interpretation_n: int = 30,
) -> PairedReport:
    if not isinstance(control, Mapping) or not isinstance(variant, Mapping):
        raise TypeError("case ID → bool mappings required")
    if not control or len(control) > 10_000 or set(control) != set(variant):
        raise ValueError("nonempty identical case ID sets required")
    if any(not isinstance(key, str) or not key for key in control):
        raise ValueError("nonempty string case IDs required")
    if any(type(value) is not bool for value in list(control.values()) + list(variant.values())):
        raise ValueError("success indicators must be booleans, not numeric values")
    if type(bootstrap_samples) is not int or not 1 <= bootstrap_samples <= 20_000:
        raise ValueError("bootstrap_samples must be 1..20000")
    if type(seed) is not int:
        raise ValueError("seed must be an integer")
    if type(min_interpretation_n) is not int or min_interpretation_n < 2:
        raise ValueError("min_interpretation_n must be >=2")

    ids = sorted(control)
    b = [control[case_id] for case_id in ids]
    v = [variant[case_id] for case_id in ids]
    delta, lo, hi = paired_delta_ci(b, v, samples=bootstrap_samples, seed=seed)
    wins = sum(not x and y for x, y in zip(b, v))
    losses = sum(x and not y for x, y in zip(b, v))
    n = len(ids)
    return PairedReport(
        n=n,
        control_successes=sum(b),
        variant_successes=sum(v),
        control_rate=round(sum(b) / n, 4),
        variant_rate=round(sum(v) / n, 4),
        delta=round(delta, 4),
        bootstrap_ci_95=(round(lo, 4), round(hi, 4)),
        wins=wins, losses=losses, ties=n - wins - losses,
        mcnemar_exact_p=round(exact_discordance_p(wins, losses), 6),
        evidence_status=(
            "exploratory_small_sample" if n < min_interpretation_n
            else "paired_benchmark_only"
        ),
        bootstrap_samples=bootstrap_samples,
        seed=seed,
    )


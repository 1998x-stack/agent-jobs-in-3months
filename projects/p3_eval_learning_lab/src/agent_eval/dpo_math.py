"""Numerically stable DPO objective illustration (no training occurs)."""
import math

def dpo_loss(chosen_log_ratio: float, rejected_log_ratio: float,
             beta: float = 0.1) -> float:
    if beta <= 0:
        raise ValueError("beta must be positive")
    z = -beta * (chosen_log_ratio - rejected_log_ratio)
    return max(z, 0.0) + math.log1p(math.exp(-abs(z)))

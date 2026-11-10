"""B10: privacy-by-construction in-memory spans, metrics and SLO reporting.

No prompts, user IDs, tokens, URLs, freeform error text or secrets are accepted.
Metric labels come from closed sets to avoid high-cardinality/privacy leaks.
Offline cost is explicitly unavailable, never fabricated.
"""
from dataclasses import dataclass
import json
import math
from threading import Lock
import time
from typing import TextIO


_OPERATIONS = frozenset({
    "http_request", "worker_run", "approval_request",
    "approval_decision", "approval_execute", "sandbox_hash",
})
_OUTCOMES = frozenset({"ok", "error", "denied", "timeout"})


@dataclass(frozen=True)
class SafeEvent:
    operation: str
    outcome: str
    duration_ms: float
    attempt: int = 0
    cost_usd: float | None = None

    def __post_init__(self) -> None:
        if self.operation not in _OPERATIONS or self.outcome not in _OUTCOMES:
            raise ValueError("unknown metric label")
        if (
            not isinstance(self.duration_ms, (int, float))
            or not math.isfinite(self.duration_ms)
            or not 0 <= self.duration_ms <= 3600_000
        ):
            raise ValueError("invalid duration")
        if type(self.attempt) is not int or not 0 <= self.attempt <= 100:
            raise ValueError("invalid attempt")
        if self.cost_usd is not None and (
            not isinstance(self.cost_usd, (int, float))
            or not math.isfinite(self.cost_usd)
            or not 0 <= self.cost_usd <= 1_000
        ):
            raise ValueError("invalid cost")


def percentile_95(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    return round(ordered[math.ceil(0.95 * len(ordered)) - 1], 3)


class SafeTelemetry:
    """Fixed-size rolling record window; metadata only."""

    def __init__(self, *, max_events: int = 1000, sink: TextIO | None = None) -> None:
        if type(max_events) is not int or not 1 <= max_events <= 10_000:
            raise ValueError("max_events must be 1..10000")
        self.max_events = max_events
        self.sink = sink
        self._lock = Lock()
        self._events: list[SafeEvent] = []

    def record(self, event: SafeEvent) -> None:
        if not isinstance(event, SafeEvent):
            raise TypeError("SafeEvent required")
        with self._lock:
            self._events.append(event)
            if len(self._events) > self.max_events:
                del self._events[:len(self._events) - self.max_events]
            if self.sink is not None:
                # Only explicitly whitelisted fields are emitted.
                self.sink.write(json.dumps({
                    "operation": event.operation,
                    "outcome": event.outcome,
                    "duration_ms": event.duration_ms,
                    "attempt": event.attempt,
                    "cost_usd": event.cost_usd,
                }, separators=(",", ":")) + "\n")

    def summary(
        self,
        *,
        operation: str | None = None,
        target_success_rate: float = 0.99,
        target_p95_ms: float = 1000.0,
        min_samples: int = 20,
    ) -> dict:
        if operation is not None and operation not in _OPERATIONS:
            raise ValueError("invalid operation filter")
        if (
            not 0 < target_success_rate <= 1
            or not 0 < target_p95_ms < 3600_000
            or type(min_samples) is not int or min_samples < 1
        ):
            raise ValueError("invalid SLO threshold")
        with self._lock:
            events = [
                e for e in self._events if operation is None or e.operation == operation
            ]
        n = len(events)
        success = sum(e.outcome == "ok" for e in events)
        p95 = percentile_95([e.duration_ms for e in events])
        enough = n >= min_samples
        return {
            "samples": n,
            "success_rate": round(success / n, 4) if n else None,
            "error_rate": round((n - success) / n, 4) if n else None,
            "p95_latency_ms": p95,
            "cost_usd_observed": (
                round(sum(e.cost_usd for e in events if e.cost_usd is not None), 6)
                if any(e.cost_usd is not None for e in events) else None
            ),
            "slo_status": (
                "insufficient_samples" if not enough else
                "met" if success / n >= target_success_rate and p95 <= target_p95_ms
                else "breached"
            ),
        }


def timed_call(
    operation: str,
    telemetry: SafeTelemetry,
    callback,
    *,
    attempt: int = 0,
):
    """Instrument a synchronous safe operation without capturing its arguments."""
    start = time.perf_counter()
    outcome = "error"
    try:
        value = callback()
        outcome = "ok"
        return value
    except PermissionError:
        outcome = "denied"
        raise
    except TimeoutError:
        outcome = "timeout"
        raise
    finally:
        telemetry.record(SafeEvent(
            operation=operation,
            outcome=outcome,
            duration_ms=(time.perf_counter() - start) * 1000,
            attempt=attempt,
        ))

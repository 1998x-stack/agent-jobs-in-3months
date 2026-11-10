"""B04: concurrency-bounded SQLite worker poller; no external broker.

Multiple threads/processes claim atomically through BEGIN IMMEDIATE.
This dispatcher limits worker count, batch size and poll cadence. It does not
promise fairness or horizontal scalability like Redis/RabbitMQ/Kafka.
"""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from threading import Event

from .run_repository import RunRepository
from .task_worker import process_one


@dataclass(frozen=True)
class BatchReport:
    processed_run_ids: tuple[str, ...]
    idle_slots: int


def run_batch(
    repository: RunRepository,
    *,
    max_jobs: int = 8,
    parallelism: int = 2,
) -> BatchReport:
    if type(max_jobs) is not int or not 1 <= max_jobs <= 64:
        raise ValueError("max_jobs must be 1..64")
    if type(parallelism) is not int or not 1 <= parallelism <= 8:
        raise ValueError("parallelism must be 1..8")
    # The actual DB transaction establishes exclusive ownership for a claim.
    with ThreadPoolExecutor(max_workers=parallelism) as pool:
        results = list(pool.map(lambda _: process_one(repository), range(max_jobs)))
    return BatchReport(
        processed_run_ids=tuple(run_id for run_id in results if run_id is not None),
        idle_slots=sum(run_id is None for run_id in results),
    )


def poll_batches(
    repository: RunRepository,
    stop_event: Event,
    *,
    parallelism: int = 2,
    batch_size: int = 8,
    poll_interval: float = 0.5,
    max_polls: int | None = None,
) -> list[BatchReport]:
    """Graceful, bounded polling loop; default CLI runs a finite batch."""
    if poll_interval <= 0 or poll_interval > 30:
        raise ValueError("poll_interval must be in (0,30]")
    if max_polls is not None and (type(max_polls) is not int or max_polls < 1):
        raise ValueError("max_polls must be a positive integer")
    history: list[BatchReport] = []
    while not stop_event.is_set():
        if max_polls is not None and len(history) >= max_polls:
            break
        report = run_batch(
            repository, max_jobs=batch_size, parallelism=parallelism
        )
        history.append(report)
        if not report.processed_run_ids:
            stop_event.wait(poll_interval)
    return history

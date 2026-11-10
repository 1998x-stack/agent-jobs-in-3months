"""Telemetry contract: do not include raw prompts, secrets or PII."""
def safe_task_event(job_id: int, status: str, attempt: int) -> dict:
    return {"job_id": job_id, "status": status, "attempt": attempt}

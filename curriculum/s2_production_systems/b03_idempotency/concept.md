# B03 · Idempotency Keys and Retry Semantics: Concepts

## What and why

Unique (tenant,key) plus SHA-256 of canonical payload guarantees deterministic request replay/conflict handling under concurrent submissions.

## Interview questions

1. What differs between submitting the same request again and retrying a failed worker?
2. Why should changed payload under same key produce 409?
3. Why do idempotent submissions not imply exactly-once side effects?

## Implementation map

- [Atomic exercise](exercise.py) · [Self-test](check_exercise.py)
- [FastAPI](../../../projects/p2_cloud_runtime/src/agent_runtime/task_api.py)
- [SQLite run repository](../../../projects/p2_cloud_runtime/src/agent_runtime/run_repository.py)
- [Offline Worker](../../../projects/p2_cloud_runtime/src/agent_runtime/task_worker.py)

## Limitations

Bearer demo mapping is not production identity. SQLite atomic request creation is not a guarantee of exactly-once external work.

## Reference

https://fastapi.tiangolo.com/tutorial/testing/ · https://docs.python.org/3/library/sqlite3.html

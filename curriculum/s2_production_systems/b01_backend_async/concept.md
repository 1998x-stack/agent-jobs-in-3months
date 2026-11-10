# B01 · FastAPI / HTTP Task Contract: Concepts

## What and why

HTTP submits tasks and returns a durable 202 receipt. Worker execution is separate from the request thread.

## Interview questions

1. What should POST/GET return when tasks are queued, done, missing or conflicting?
2. Why does API authentication derive tenant/actor instead of trusting model output?
3. How is TestClient different from a real listening server?

## Implementation map

- [Atomic exercise](exercise.py) · [Self-test](check_exercise.py)
- [FastAPI](../../../projects/p2_cloud_runtime/src/agent_runtime/task_api.py)
- [SQLite run repository](../../../projects/p2_cloud_runtime/src/agent_runtime/run_repository.py)
- [Offline Worker](../../../projects/p2_cloud_runtime/src/agent_runtime/task_worker.py)

## Limitations

Bearer demo mapping is not production identity. SQLite atomic request creation is not a guarantee of exactly-once external work.

## Reference

https://fastapi.tiangolo.com/tutorial/testing/ · https://docs.python.org/3/library/sqlite3.html

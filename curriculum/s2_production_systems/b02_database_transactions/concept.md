# B02 · SQLite Transactions / Atomicity: Concepts

## What and why

BEGIN IMMEDIATE serializes SQLite writers; transaction rollback means task+audit writes succeed together or not at all.

## Interview questions

1. What does BEGIN IMMEDIATE acquire?
2. Why must unique constraints live in the database?
3. Why is SQLite insufficient for a distributed production task queue?

## Implementation map

- [Atomic exercise](exercise.py) · [Self-test](check_exercise.py)
- [FastAPI](../../../projects/p2_cloud_runtime/src/agent_runtime/task_api.py)
- [SQLite run repository](../../../projects/p2_cloud_runtime/src/agent_runtime/run_repository.py)
- [Offline Worker](../../../projects/p2_cloud_runtime/src/agent_runtime/task_worker.py)

## Limitations

Bearer demo mapping is not production identity. SQLite atomic request creation is not a guarantee of exactly-once external work.

## Reference

https://fastapi.tiangolo.com/tutorial/testing/ · https://docs.python.org/3/library/sqlite3.html

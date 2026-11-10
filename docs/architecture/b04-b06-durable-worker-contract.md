# ADR · B04–B06 Durable Worker and Recovery

## Queue
SQLite BEGIN IMMEDIATE serializes claims. Concurrent Worker slots are bounded by max_jobs and parallelism; idle polling uses a cancellation Event. This is a local durable queue, not an external broker.

## Lease and retry
Each claim has a random fencing token. Only the current unexpired token can renew a lease, write a checkpoint, or commit a result. RetryableWorkError schedules a future available_at using bounded exponential backoff and optional deterministic jitter. Permanent failures remain failed, and max three attempts are allowed.

## Checkpoint contract
The run_checkpoints table is unique on (run_id, step_key). Supported keys are plan and task-01 through task-03. Checkpoints are immutable after commit. Each task checkpoint stores a verified source-extract result from the offline P1 Agent Team, not arbitrary model assertions.

## Crash recovery
A simulated hard crash occurs after the first task checkpoint commits. The next Worker reopens SQLite after the previous lease expires, reuses committed plan/task results and executes only missing tasks. An old worker cannot commit after token expiry.

## No exactly-once side effects
Checkpoints prevent replay of completed committed steps, but a crash after an external effect and before checkpoint commit may repeat that effect. This version uses fictional read-only tools, not payments. Production needs destination idempotency, transactional outbox, encrypted checkpoint store, real auth, service monitoring, secure heartbeats and external broker.

## State transitions
queued -> running (fenced claim)
running -> queued (explicit retryable error plus delay)
running -> running (lease expiry and new claim)
running -> failed (permanent error or exhausted attempts)
running -> completed (fenced DB commit)

## Verification
Run the offline module agent_runtime.durability_demo or pytest projects/p2_cloud_runtime/tests/test_durable_workers.py. CI runs both.

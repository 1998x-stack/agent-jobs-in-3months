# P2 · Agent Cloud Runtime

**Goal:** FastAPI task creation/status/retry, SQLite transactions and bounded offline P1 execution. This is a local teaching demo.

## Two code paths

- Original `storage.py`, `approval.py`, `workflow.py`, `demo.py`: preserved previous P2 reference.
- `task_api.py`: FastAPI endpoint and demo Bearer Token identity boundary.
- `run_repository.py`: atomic transactions, unique idempotency keys, request fingerprints and worker fencing.
- `task_worker.py`: separate offline worker integrating P1 TeamCoordinator.
- `api_demo.py`: in-process HTTP → SQLite → Worker → GET, zero network/API keys.
- `tests/test_task_api.py`: HTTP contracts, concurrency, tenant authorization, retries and stale worker rejection.

## Quick demo (no LLM charges)

```bash
python -m pip install -e '.[dev,api]'
PYTHONPATH=projects/p1_agent_harness/src:projects/p2_cloud_runtime/src python -m agent_runtime.api_demo
python -m pytest
```

Expected: POST 202 → duplicate POST 200 with the SAME run ID → worker executes P1 read-only Agent → GET completed with verified citations.

## Optional localhost server

```bash
export AGENT_DEMO_API_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
export AGENT_RUN_DB=./agent-runs.sqlite3
export AGENT_DEMO_TENANT=demo-tenant
export AGENT_DEMO_USER=demo-user
PYTHONPATH=projects/p1_agent_harness/src:projects/p2_cloud_runtime/src uvicorn agent_runtime.task_api:create_app_from_env --factory --host 127.0.0.1 --port 8000
```

In another shell, reuse the same token:

```bash
curl -X POST http://127.0.0.1:8000/v1/runs -H "Authorization: Bearer $AGENT_DEMO_API_TOKEN" -H 'Idempotency-Key: demo-run-000001' -H 'Content-Type: application/json' -d '{"question":"refund proposal human approval"}'
PYTHONPATH=projects/p1_agent_harness/src:projects/p2_cloud_runtime/src python -m agent_runtime.task_worker --db ./agent-runs.sqlite3
```

Use the returned run_id for GET /v1/runs/{run_id}, with Bearer auth.

## HTTP contract

| Endpoint | Status and semantics |
|---|---|
| GET /healthz | unauthenticated health check |
| POST /v1/runs | 202 new, 200 same-key/same-canonical-request replay, 409 conflicting replay |
| GET /v1/runs/{id} | 200 actor-owned, 404 otherwise |
| POST /v1/runs/{id}/retry | failed→queued, queued no-op, completed/running/max attempts→409 |

Request fields: `question` (1..600 chars), `max_tasks` (1..3), `max_context_chars` (800..8000). New POST needs Authorization: Bearer and Idempotency-Key.

## Correctness boundaries

- Tenant and user are derived by service-configured demo Bearer token, NOT client headers or model arguments.
- SQLite `BEGIN IMMEDIATE` + `UNIQUE(tenant_id, request_key)` serializes competing submissions; fingerprints detect changed payloads.
- Worker uses an expiring lease and unique fencing token; stale workers cannot commit database results.
- Retry after worker failure is limited to three attempts. A completed run is never executed by retry.
- All worker operations use offline, synthetic, read-only P1 tools. Failures store sanitized `worker_failed`, not exception text.

**Not production ready:** static token is NOT OAuth/OIDC; bind only on localhost. SQLite fencing is not exactly-once external execution. Use destination idempotency, transactional outbox, reconciliation, broker, secrets and observability for production. No real payment tools or real customer data are supported.

Official references: https://fastapi.tiangolo.com/tutorial/testing/ · https://docs.python.org/3/library/sqlite3.html.

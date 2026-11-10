# W05 · FastAPI, SQL Transactions and Idempotency

## Atomic skills

- [B01 HTTP / FastAPI](../../curriculum/s2_production_systems/b01_backend_async/README.md)
- [B02 Database Transactions](../../curriculum/s2_production_systems/b02_database_transactions/README.md)
- [B03 Idempotency](../../curriculum/s2_production_systems/b03_idempotency/README.md)

## Delivered

- [x] POST /runs + GET status + bounded retry with strict Pydantic schemas
- [x] server-configured demo bearer mapping → tenant/user
- [x] SQLite atomic insert, rollback, database unique key and fingerprint
- [x] concurrent duplicate submission and worker competition tests
- [x] P1 TeamCoordinator executed from offline worker and recorded verified citations
- [x] stale lease completion rejected; failed retries bounded to three
- [ ] production auth, TLS, Postgres, durable message broker, transaction outbox
- [ ] SLO, audit, load testing and model cost metrics

## Acceptance

```bash
python -m pip install -e '.[dev,api]'
python -m pytest
PYTHONPATH=projects/p1_agent_harness/src:projects/p2_cloud_runtime/src python -m agent_runtime.api_demo
python scripts/check_progress.py
```

HTTP task receipt is not external payment idempotency. An expired lease may permit a worker to repeat *read-only* work.

Evidence: `projects/p2_cloud_runtime/tests/test_task_api.py`; PR: TODO.

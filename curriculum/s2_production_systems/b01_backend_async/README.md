# B01 · FastAPI / HTTP Task Contract

**Status:** atomic exercise implemented and integrated into the P2 API example.

## Objective

HTTP submits tasks and returns a durable 202 receipt. Worker execution is separate from the request thread.

## Learning loop

1. Read [concept.md](concept.md) and review state/transaction boundaries.
2. Inspect [exercise.py](exercise.py) and explain success and failure behavior.
3. Run `python check_exercise.py` from this directory.
4. Compare your code to [P2 Runtime API](../../../projects/p2_cloud_runtime/README.md).
5. Run `python -m pytest` at the repository root.

## Acceptance

- [x] Runnable teaching micro-exercise
- [x] Boundary and failure-path self-test
- [x] P2 full API/transaction/idempotency integration
- [ ] Rewrite independently and capture a failure trace
- [ ] Propose how to productionize this component

All data is synthetic and local. No live model calls are used in CI.

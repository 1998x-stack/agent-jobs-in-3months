# W08 · Observability, Metrics & SLO

## Unit

- [B10 Observability & SLO](../../curriculum/s2_production_systems/b10_observability_slo/README.md)

## Engineering deliverables

- [x] Structured SafeEvent schema with allowlisted low-cardinality labels
- [x] Fixed rolling-window SafeTelemetry and optional JSONL sink
- [x] HTTP, approval, sandbox and optional worker duration/outcome instrumentation
- [x] Operational samples, error rate, nearest-rank p95 and sample-qualified SLO
- [x] Output does not contain raw prompts, credentials, user info, query paths or stacktraces
- [x] Offline token/cost data absent => explicit unknown cost instead of invented price
- [ ] OpenTelemetry spans to OTLP backend
- [ ] Real per-model token/cost data and trace sampling policies
- [ ] Production SLI thresholds, burn-rate alerts, alerts-to-runbooks and long-window metrics

## Run

```bash
PYTHONPATH=projects/p1_agent_harness/src:projects/p2_cloud_runtime/src python -m agent_runtime.governance_demo
python -m pytest projects/p2_cloud_runtime/tests/test_governance_security.py
```

## SLO scope

This is a demonstration of metric shape and p95 calculation, not an uptime or latency claim about an internet-facing service. Defaults require at least 20 events before reporting met/breached.

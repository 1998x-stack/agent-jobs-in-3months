# Observability — TODO

Define span names: `agent.run`, `agent.plan`, `agent.tool_call`, `runtime.claim`, `runtime.complete`, `eval.grade`.
Record: run id, attempt, tool name, duration, cost estimate, sanitized error category, tenant-safe correlation ID.
Never send raw private prompts or credentials to telemetry. Add Grafana dashboards and SLO alerts once data schema is stable.

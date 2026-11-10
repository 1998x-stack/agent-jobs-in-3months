# P3 · C01–C03 Evaluation Data / Gold State / Trajectory Contract

## Source of Truth

Source contracts are strictly versioned: `agent-eval.v1` for JSONL and `agent-eval-report.v1` for deterministic reports. The benchmark contains synthetic read-only policy tasks only.

## Evaluation pipeline

1. Validate every JSONL record using strict Pydantic schema, reject unknown keys and duplicates, check group/split and normalized question leakage.
2. Calculate a stable SHA-256 digest over canonicalized sorted cases so any changes to labels appear in the report.
3. For each case, create a new temporary SQLite database, submit a real P2 task under a synthetic tenant/user, and execute via the P2 Worker into P1 TeamCoordinator.
4. Read final state with a trusted scope, persisted Checkpoint names, citation IDs and synthetic receipt count; compare with Gold State.
5. Read P2 Checkpoint payloads and the actual A04 tool action names persisted by P1; project to redacted TraceEvents in stable workflow order.
6. Score ordered tools, forbidden calls, optional exact parameter constraints, checkpoint coverage and terminal status. Missing native tool arguments remain `None` and fail any requested parameter assertion.
7. Emit only case IDs, scenario, pass/fail, taxonomy labels, aggregate counts and dataset digest, not prompt, tenant ID, raw model output or tool observation.

## Failure Taxonomy

Primary label is a deterministic precedence, not inferred causal diagnosis: unsafe_tool > wrong_run_state > side_effect_mismatch > wrong_result_state > citation_mismatch > missing_or_misordered_tool > tool_parameter_mismatch > checkpoint_mismatch > terminal_trace_mismatch > malformed_trajectory.

## Provenance and information-loss honesty

Native P1 TraceStep contains action name and metadata only. P2 Checkpoint records source-observed A04 tool action names, not tool arguments, tool result bodies or complete timestamped call chains. Reconstructed P2 order is based on fixed checkpoint keys, not authoritative event timestamps. Do not claim full trajectory fidelity or semantic provenance.

## Data leakage and holdout

13 synthetic cases: train=4, dev=4, holdout=5, separated by policy document group. This prevents exact duplicates and cross-split group contamination in this tiny fixture. It does NOT guarantee that related policy concepts or prompts are statistically independent, or that any real-world generalization can be inferred.

## Scope, safety, and CI

No live LLM calls, external payments, unauthorized tenant access or real user records. All results use read-only synthetic data. CI runs both holdout and all-case regression gate, plus tests injecting unsafe tool steps, wrong parameters, corrupted records, missing Gold checkpoints and cross-tenant reads.

## Follow-up

Record safe tool-argument metadata with schema version and tenancy; add evaluator agreement studies, semantic verification, true held-out distributions, confidence intervals/paired A/B and failure-mining dashboards.

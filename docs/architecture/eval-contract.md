# Eval Contract

## Task case fields

- `id`: immutable stable task ID
- `expected_outcome`: exact deterministic oracle for toy experiment
- `required_tools`: tool names that must appear in valid trace
- `forbidden_tools`: tools that must never be called
- `tags`: scenario stratification

## Production extensions (TODO)

- Input state, environment snapshot, final state diff, tool arguments, timeouts, allowed retries.
- Agent version, model version, prompt hash, dataset version, random seed.
- Grader version, human adjudication, false-positive checks and confidence intervals.
- Identity, permission and data retention policy for traces.

A single synthetic test must not be used to claim a universal model performance gain.

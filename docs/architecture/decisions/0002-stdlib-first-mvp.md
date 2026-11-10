# ADR-0002 · Standard Library First MVP

**Status:** Accepted for the learning scaffold.

## Decision

Keep the initial three demonstration projects runnable with the Python stdlib and pytest, without API keys, hosted models or cloud accounts.

## Why

Isolates control-flow, state, retry and grading concepts from API variability and avoids charging for basic tests.

## Consequences

Production authentication, model inference, RAG, queue distribution, token metering and sandboxing remain explicit TODOs; the MVP cannot be claimed as production ready.

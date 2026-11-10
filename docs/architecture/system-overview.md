# System Overview

## Components

1. Planner proposes actions; never executes tools directly.
2. ToolRegistry validates availability; production implementation must additionally validate schemas, identity and scope.
3. Runtime stores task state and fenced lease ownership; external effects need idempotent protocols.
4. Eval Lab reads versioned, sanitized traces and task outcomes, then compares versions.

## Primary data flow

User goal → Agent Loop → Tool proposal → Authorization → Execution → Trace → Durable state → Dataset / Oracle → Evaluations → Design improvement.

## Trust boundaries

- LLM output, retrieved documents and tool responses are untrusted.
- Worker database credentials and user OAuth credentials must be separate.
- Approval is an authorization event, not an LLM suggestion.
- Offline toy planner and SQLite store must not be deployed for financial operations.

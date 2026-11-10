# ADR · B07–B10 Approval, RBAC, Fixed-code Subprocess & Safe Telemetry

## Explicit trust boundaries

| Source | Trust | Guard |
|---|---|---|
| HTTP Authorization bearer | Local demo credential | Server-configured token-to-Principal mapping |
| Model response and tool output | Untrusted | P1 source verification, never interpreted as approval |
| HTTP JSON body | Untrusted | Strict Pydantic schema, extra=forbid |
| Principal roles | Trusted configuration only | Closed RBAC allowlist |
| SQLite approval and receipt | Transactional | Four-eyes state machine and receipt uniqueness |
| Sandbox text | Untrusted | Fixed-code tool allowlist, resource / time / input bounds |
| Telemetry | Derived safe metadata | Closed operation/outcome labels and numeric fields only |

## B07 approval state machine

pending → approved or denied. Approved → consumed on creation of exactly one synthetic receipt. Replaying consumed returns the original receipt. Rejected/denied approval cannot execute. Request requires completed, supported run owned by the actor. Requester, reviewer and executor must be distinct trusted users. Approval database writes and audit inserts are atomic.

Attack checks include self-approval, same-tenant wrong role, cross-tenant visibility, denied actions, unsupported run requests and duplicate execution. Audit only stores actor ID and event metadata, never prompts or tokens. Only release_demo_receipt is allowlisted; no actual payment tools exist.

## B08 auth boundary

Role-to-permission is a closed static dictionary. Principal comes from the server's configured identity map. HTTP user/tenant/model inputs cannot create roles. 401 is used for unknown token, 403 for known actor without permission, and 404 for hidden cross-tenant/other-user objects.

Static tokens are NOT enterprise OAuth/OIDC; production requires signed-claim issuer, audience, expiry and JWKS checks, revocation, TLS, identity lifecycle and secure audit retention.

## B09 limited subprocess

Only fixed hash_text/count_words Python code may execute. Parent starts a python -I -S process with temporary cwd, a small env allowlist, bounded input/output, timeout, and static child-side RLIMIT_CPU/AS/FSIZE on POSIX.

**This is not secure untrusted-code sandboxing.** Same OS user, filesystem, and network namespace remain accessible. No seccomp, containers, microVMs or egress control. Do not run arbitrary source code or sensitive data in this example.

## B10 operational metrics

SafeEvent fields are operation, outcome, duration_ms, attempt and optional cost_usd; labels are allowlisted and values bounded. A rolling in-process buffer produces count, error/success rate, nearest-rank p95 and SLO status with min sample guard. Offline cost is unknown (null), not invented. Optional JSONL output does not accept raw paths, prompts, tokens, user IDs or exception text.

These measurements are example shapes, not durable traces, real model cost tracking, uptime measurements, SLO certification or production-grade alerting.

## Reproduction

Run `python -m pytest` and `PYTHONPATH=projects/p1_agent_harness/src:projects/p2_cloud_runtime/src python -m agent_runtime.governance_demo` after installing dev dependencies.

## Follow-up production work

OIDC/JWKS + rotation, secure approval policy and independent reviewers, append-only encrypted audit store, sandbox namespaces/seccomp or microVM, egress controls, OpenTelemetry/OTLP, retention policies and SLO alerting.

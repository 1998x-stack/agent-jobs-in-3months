# Threat Model (Educational Baseline)

| Risk | Attack surface | Baseline defense | Test idea |
|---|---|---|---|
| Prompt injection | RAG / tool output | treat retrieved text as data | inject fake tool instruction in policy text |
| Tool misuse | Agent action | allowlist + schema + policy | propose unknown tool |
| Cross-tenant reads | Memory / DB | tenant-scoped query | access another tenant's resource |
| Replay / duplicate side effects | retries | operation idempotency | duplicate approval / submit |
| Stale worker updates | leases | fencing token | complete after lease reclaimed |
| Arbitrary code execution | code tool | restricted sandbox / egress controls | attempt network and file escape |

TODO: STRIDE review, OWASP LLM Top 10 mapping, signing and approval audit, secrets threat review.
Security claims must be validated in the chosen deployment environment.

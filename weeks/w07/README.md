# W07 · Approval, Authorization & Sandbox

## Units

- [B07 Human-in-the-Loop](../../curriculum/s2_production_systems/b07_human_approval/README.md)
- [B08 RBAC / Tenant Scope](../../curriculum/s2_production_systems/b08_identity_authorization/README.md)
- [B09 Fixed-code Subprocess](../../curriculum/s2_production_systems/b09_sandbox/README.md)

## Engineering deliverables

- [x] SQLite pending/approved/denied/consumed state machine and immutable audit events
- [x] Requester, Approver, Executor must be three independent users
- [x] No execution before approval, after denial, or across tenants
- [x] Synthetic receipt created transactionally only once; no real payment integration
- [x] Role-to-permission allowlist with service-provided identity binding
- [x] Fixed-code Python -I -S subprocess, time and POSIX resource limits
- [x] FastAPI route contracts and offline negative/security tests
- [ ] Real OIDC/JWKS token verification, role policies from trusted IdP
- [ ] Hardened container/process isolation and egress control
- [ ] Audit retention/storage governance and external transaction outbox

## Reproduction

```bash
python -m pip install -e '.[dev,api]'
PYTHONPATH=projects/p1_agent_harness/src:projects/p2_cloud_runtime/src python -m agent_runtime.governance_demo
python -m pytest projects/p2_cloud_runtime/tests/test_governance_security.py
```

## Security boundary

Static demo tokens are local-only; no production auth or trusted untrusted-code sandbox. Never process real customers or approve financial transfers in this project.

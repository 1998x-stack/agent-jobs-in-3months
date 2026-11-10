"""B08: server-bound scoped principals and explicit least-privilege RBAC.

Principals are created by trusted application configuration, never by model
output, request JSON or unverified JWT claims. Legacy MemoryScope tokens are
mapped to the operator role for backward compatibility.
This is NOT OAuth/OIDC, JWKS verification or enterprise identity.
"""
from dataclasses import dataclass

from agent_harness.scoped_memory import MemoryScope


_ROLE_PERMISSIONS: dict[str, frozenset[str]] = {
    "viewer": frozenset({"runs:read"}),
    "observer": frozenset({"telemetry:read"}),
    "operator": frozenset({
        "runs:read", "runs:submit", "runs:retry", "approvals:request",
    }),
    "approver": frozenset({"approvals:read", "approvals:decide"}),
    "executor": frozenset({"approvals:read", "approvals:execute", "sandbox:hash"}),
}


@dataclass(frozen=True)
class Principal:
    scope: MemoryScope
    roles: frozenset[str]

    def __post_init__(self) -> None:
        if not isinstance(self.scope, MemoryScope):
            raise TypeError("principal scope must come from trusted application configuration")
        if not isinstance(self.roles, frozenset) or not self.roles:
            raise ValueError("principal must have at least one role")
        if not self.roles.issubset(_ROLE_PERMISSIONS):
            raise ValueError("unknown role")

    @classmethod
    def operator(cls, scope: MemoryScope) -> "Principal":
        return cls(scope=scope, roles=frozenset({"operator"}))

    def allows(self, permission: str) -> bool:
        return any(permission in _ROLE_PERMISSIONS[role] for role in self.roles)


def require_permission(principal: Principal, permission: str) -> None:
    if not isinstance(principal, Principal):
        raise TypeError("authenticated principal required")
    if not principal.allows(permission):
        raise PermissionError("permission denied")


def authorize_tenant(principal: Principal, tenant: str, permission: str) -> None:
    require_permission(principal, permission)
    if principal.scope.tenant_id != tenant:
        raise PermissionError("cross-tenant access denied")

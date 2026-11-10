"""B08: least-privilege role and tenant check; no unverified JWT claims."""
from typing import Any


_PERMISSIONS = {
    "viewer": {"runs:read"},
    "operator": {"runs:submit", "runs:read", "runs:retry", "approvals:request"},
    "approver": {"approvals:decide"},
    "executor": {"approvals:execute"},
}


def solve(input_data: dict[str, Any]) -> dict[str, Any]:
    actor_tenant = input_data.get("actor_tenant")
    target_tenant = input_data.get("target_tenant")
    role = input_data.get("role")
    permission = input_data.get("permission")
    if not all(isinstance(x, str) and x for x in (
        actor_tenant, target_tenant, role, permission
    )):
        raise ValueError("tenant and authorization fields required")
    if role not in _PERMISSIONS:
        raise PermissionError("unknown role")
    if actor_tenant != target_tenant or permission not in _PERMISSIONS[role]:
        raise PermissionError("access denied")
    return {"authorized": True, "role": role, "permission": permission}

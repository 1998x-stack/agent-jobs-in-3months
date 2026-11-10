"""Placeholder for real policy engine, identity and signed tool grants."""
def require_tenant(subject_tenant: str, resource_tenant: str) -> None:
    if not subject_tenant or subject_tenant != resource_tenant:
        raise PermissionError("tenant access denied")

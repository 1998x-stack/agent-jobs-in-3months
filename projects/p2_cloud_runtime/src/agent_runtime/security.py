"""Teaching tenant guard. TODO: authenticated identities and credential broker."""
def authorize(actor_tenant: str, job_tenant: str) -> None:
    if not actor_tenant or actor_tenant != job_tenant:
        raise PermissionError("cross-tenant operation denied")

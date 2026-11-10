"""B01: FastAPI task submission, status and safe-retry boundary.

No task is executed in an HTTP request. Worker processing runs separately.
An identity is derived from an application-injected demo token mapping,
NOT from an LLM, user-controlled tenant header or JSON body.
Static tokens in this demo are NOT production OAuth/OIDC authentication.
"""
from collections.abc import Mapping
import os
import secrets
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Response
from pydantic import BaseModel, ConfigDict, Field, field_validator

from agent_harness.scoped_memory import MemoryScope
from .run_repository import RunConflict, RunMissing, RunRecord, RunRepository


class SubmitRun(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    question: str = Field(min_length=1, max_length=600)
    max_tasks: int = Field(default=3, ge=1, le=3)
    max_context_chars: int = Field(default=2200, ge=800, le=8000)

    @field_validator("question")
    @classmethod
    def trim_question(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("question cannot be blank")
        return value.strip()


class RunView(BaseModel):
    run_id: str
    status: str
    attempt: int
    question: str
    result: dict | None
    error_code: str | None

    @classmethod
    def from_record(cls, record: RunRecord) -> "RunView":
        # Do not return tenant/user IDs, credentials, or idempotency keys.
        return cls(
            run_id=record.run_id, status=record.status, attempt=record.attempt,
            question=record.question, result=record.result,
            error_code=record.error_code,
        )


def create_app(
    db_path: str,
    *,
    token_identities: Mapping[str, MemoryScope],
) -> FastAPI:
    if not token_identities:
        raise ValueError("at least one demo identity token is required")
    for token, scope in token_identities.items():
        if not isinstance(token, str) or len(token) < 16 or not isinstance(scope, MemoryScope):
            raise ValueError("tokens must be >=16 chars and map to trusted MemoryScope")
    credentials = dict(token_identities)
    repository = RunRepository(db_path)
    app = FastAPI(
        title="P2 Agent Runtime - B01/B03 Teaching API",
        version="0.1.0",
        description="Synthetic read-only Agent jobs. NOT production auth or a payments API.",
    )

    def get_identity(
        authorization: Annotated[str | None, Header(alias="Authorization")] = None,
    ) -> MemoryScope:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Bearer authentication required")
        supplied = authorization.removeprefix("Bearer ")
        # Compare opaque bearer credentials, not client-supplied tenant names.
        for expected, scope in credentials.items():
            if secrets.compare_digest(supplied, expected):
                return scope
        raise HTTPException(status_code=401, detail="invalid bearer token")

    Actor = Annotated[MemoryScope, Depends(get_identity)]

    @app.get("/healthz")
    def healthcheck() -> dict:
        return {"status": "ok"}

    @app.post("/v1/runs", response_model=RunView, status_code=202)
    def submit(
        payload: SubmitRun,
        response: Response,
        actor: Actor,
        idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
    ) -> RunView:
        if idempotency_key is None:
            raise HTTPException(status_code=400, detail="Idempotency-Key header required")
        try:
            record, created = repository.submit(
                actor,
                idempotency_key=idempotency_key,
                question=payload.question,
                max_tasks=payload.max_tasks,
                max_context_chars=payload.max_context_chars,
            )
        except RunConflict as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        response.status_code = 202 if created else 200
        return RunView.from_record(record)

    @app.get("/v1/runs/{run_id}", response_model=RunView)
    def status(run_id: str, actor: Actor) -> RunView:
        record = repository.get(actor, run_id)
        if record is None:
            raise HTTPException(status_code=404, detail="run not found")
        return RunView.from_record(record)

    @app.post("/v1/runs/{run_id}/retry", response_model=RunView, status_code=202)
    def retry(run_id: str, actor: Actor) -> RunView:
        try:
            record = repository.retry(actor, run_id)
        except RunMissing as exc:
            raise HTTPException(status_code=404, detail="run not found") from exc
        except RunConflict as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return RunView.from_record(record)

    return app


def create_app_from_env() -> FastAPI:
    """CLI factory: requires explicit local demo token, never creates one secretly."""
    token = os.getenv("AGENT_DEMO_API_TOKEN", "")
    if len(token) < 16:
        raise RuntimeError("set AGENT_DEMO_API_TOKEN (>=16 chars) to run API locally")
    path = os.getenv("AGENT_RUN_DB", "./agent-runs.sqlite3")
    tenant = os.getenv("AGENT_DEMO_TENANT", "demo-tenant")
    user = os.getenv("AGENT_DEMO_USER", "demo-user")
    return create_app(path, token_identities={token: MemoryScope(tenant, user)})

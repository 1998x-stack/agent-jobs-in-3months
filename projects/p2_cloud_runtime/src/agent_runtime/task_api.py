"""B01: FastAPI task submission, status and safe-retry boundary.

No task is executed in an HTTP request. Worker processing runs separately.
An identity is derived from an application-injected demo token mapping,
NOT from an LLM, user-controlled tenant header or JSON body.
Static tokens in this demo are NOT production OAuth/OIDC authentication.
"""
from collections.abc import Mapping
import os
import secrets
import time
from typing import Annotated, Literal

from fastapi import Depends, FastAPI, Header, HTTPException, Response
from pydantic import BaseModel, ConfigDict, Field, field_validator

from agent_harness.scoped_memory import MemoryScope
from .approval_gate import ApprovalConflict, ApprovalGate, ApprovalMissing, ApprovalRecord
from .identity import Principal, require_permission
from .observability import SafeEvent, SafeTelemetry, timed_call
from .sandbox import SandboxRunner, SandboxViolation
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


class ApprovalDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    decision: Literal["approved", "denied"]


class SandboxHashInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    text: str = Field(min_length=1, max_length=512)


class ApprovalView(BaseModel):
    approval_id: str
    run_id: str
    action: str
    status: str
    requested_by: str
    approved_by: str | None
    receipt_id: str | None

    @classmethod
    def from_record(cls, value: ApprovalRecord) -> "ApprovalView":
        return cls(**vars(value))


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
    token_identities: Mapping[str, MemoryScope | Principal],
    telemetry: SafeTelemetry | None = None,
) -> FastAPI:
    if not token_identities:
        raise ValueError("at least one demo identity token is required")
    credentials: dict[str, Principal] = {}
    for token, identity in token_identities.items():
        if not isinstance(token, str) or len(token) < 16:
            raise ValueError("demo tokens must contain >=16 chars")
        if isinstance(identity, MemoryScope):
            credentials[token] = Principal.operator(identity)
        elif isinstance(identity, Principal):
            credentials[token] = identity
        else:
            raise ValueError("demo identity must be an application-bound scope or principal")
    repository = RunRepository(db_path)
    approvals = ApprovalGate(repository)
    sandbox = SandboxRunner()
    metrics = telemetry if telemetry is not None else SafeTelemetry()
    app = FastAPI(
        title="P2 Agent Runtime - B01/B03 Teaching API",
        version="0.1.0",
        description="Synthetic read-only Agent jobs. NOT production auth or a payments API.",
    )

    app.state.telemetry = metrics

    @app.middleware("http")
    async def observe_requests(request, call_next):
        # Only low-cardinality status and duration; never paths, tokens or bodies.
        start = time.perf_counter()
        outcome = "error"
        try:
            response = await call_next(request)
            outcome = "ok" if response.status_code < 400 else (
                "denied" if response.status_code in (401, 403) else "error"
            )
            return response
        finally:
            metrics.record(SafeEvent(
                "http_request", outcome,
                (time.perf_counter() - start) * 1000,
            ))

    def get_identity(
        authorization: Annotated[str | None, Header(alias="Authorization")] = None,
    ) -> Principal:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Bearer authentication required")
        supplied = authorization.removeprefix("Bearer ")
        # Compare opaque bearer credentials, not client-supplied tenant names.
        for expected, principal in credentials.items():
            if secrets.compare_digest(supplied, expected):
                return principal
        raise HTTPException(status_code=401, detail="invalid bearer token")

    Actor = Annotated[Principal, Depends(get_identity)]

    def allowed(actor: Principal, permission: str) -> MemoryScope:
        try:
            require_permission(actor, permission)
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail="permission denied") from exc
        return actor.scope

    def approval_errors(fn):
        try:
            return fn()
        except ApprovalMissing as exc:
            raise HTTPException(status_code=404, detail="approval not found") from exc
        except ApprovalConflict as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail="permission denied") from exc

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
        scope = allowed(actor, "runs:submit")
        if idempotency_key is None:
            raise HTTPException(status_code=400, detail="Idempotency-Key header required")
        try:
            record, created = repository.submit(
                scope,
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
        scope = allowed(actor, "runs:read")
        record = repository.get(scope, run_id)
        if record is None:
            raise HTTPException(status_code=404, detail="run not found")
        return RunView.from_record(record)

    @app.post("/v1/runs/{run_id}/retry", response_model=RunView, status_code=202)
    def retry(run_id: str, actor: Actor) -> RunView:
        scope = allowed(actor, "runs:retry")
        try:
            record = repository.retry(scope, run_id)
        except RunMissing as exc:
            raise HTTPException(status_code=404, detail="run not found") from exc
        except RunConflict as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return RunView.from_record(record)



    @app.post("/v1/runs/{run_id}/approvals", response_model=ApprovalView, status_code=202)
    def request_approval(run_id: str, actor: Actor, response: Response) -> ApprovalView:
        allowed(actor, "approvals:request")
        result, created = approval_errors(lambda: timed_call(
            "approval_request", metrics, lambda: approvals.request(actor, run_id)
        ))
        response.status_code = 202 if created else 200
        return ApprovalView.from_record(result)

    @app.get("/v1/approvals/{approval_id}", response_model=ApprovalView)
    def approval_status(approval_id: str, actor: Actor) -> ApprovalView:
        result = approval_errors(lambda: approvals.get(actor, approval_id))
        return ApprovalView.from_record(result)

    @app.post("/v1/approvals/{approval_id}/decision", response_model=ApprovalView)
    def decide_approval(
        approval_id: str, payload: ApprovalDecision, actor: Actor
    ) -> ApprovalView:
        allowed(actor, "approvals:decide")
        result = approval_errors(lambda: timed_call(
            "approval_decision", metrics,
            lambda: approvals.decide(actor, approval_id, decision=payload.decision)
        ))
        return ApprovalView.from_record(result)

    @app.post("/v1/approvals/{approval_id}/execute", response_model=ApprovalView)
    def execute_approved_receipt(approval_id: str, actor: Actor) -> ApprovalView:
        allowed(actor, "approvals:execute")
        result = approval_errors(lambda: timed_call(
            "approval_execute", metrics,
            lambda: approvals.execute(actor, approval_id)
        ))
        return ApprovalView.from_record(result)

    @app.post("/v1/sandbox/hash")
    def sandbox_hash(payload: SandboxHashInput, actor: Actor) -> dict:
        allowed(actor, "sandbox:hash")
        try:
            return timed_call(
                "sandbox_hash", metrics,
                lambda: sandbox.run("hash_text", payload.text)
            )
        except SandboxViolation as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/v1/observability/summary")
    def observability_summary(actor: Actor) -> dict:
        allowed(actor, "telemetry:read")
        return metrics.summary()

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

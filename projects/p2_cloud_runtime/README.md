# P2 · Agent Cloud Runtime

**Goal:** FastAPI task creation/status/retry, SQLite transactions and bounded offline P1 execution. This is a local teaching demo.

## Two code paths

- Original `storage.py`, `approval.py`, `workflow.py`, `demo.py`: preserved previous P2 reference.
- `task_api.py`: FastAPI endpoint and demo Bearer Token identity boundary.
- `run_repository.py`: atomic transactions, unique idempotency keys, request fingerprints and worker fencing.
- `task_worker.py`: separate offline worker integrating P1 TeamCoordinator.
- `api_demo.py`: in-process HTTP → SQLite → Worker → GET, zero network/API keys.
- `tests/test_task_api.py`: HTTP contracts, concurrency, tenant authorization, retries and stale worker rejection.

## Quick demo (no LLM charges)

```bash
python -m pip install -e '.[dev,api]'
PYTHONPATH=projects/p1_agent_harness/src:projects/p2_cloud_runtime/src python -m agent_runtime.api_demo
python -m pytest
```

Expected: POST 202 → duplicate POST 200 with the SAME run ID → worker executes P1 read-only Agent → GET completed with verified citations.

## Optional localhost server

```bash
export AGENT_DEMO_API_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
export AGENT_RUN_DB=./agent-runs.sqlite3
export AGENT_DEMO_TENANT=demo-tenant
export AGENT_DEMO_USER=demo-user
PYTHONPATH=projects/p1_agent_harness/src:projects/p2_cloud_runtime/src uvicorn agent_runtime.task_api:create_app_from_env --factory --host 127.0.0.1 --port 8000
```

In another shell, reuse the same token:

```bash
curl -X POST http://127.0.0.1:8000/v1/runs -H "Authorization: Bearer $AGENT_DEMO_API_TOKEN" -H 'Idempotency-Key: demo-run-000001' -H 'Content-Type: application/json' -d '{"question":"refund proposal human approval"}'
PYTHONPATH=projects/p1_agent_harness/src:projects/p2_cloud_runtime/src python -m agent_runtime.task_worker --db ./agent-runs.sqlite3
```

Use the returned run_id for GET /v1/runs/{run_id}, with Bearer auth.

## HTTP contract

| Endpoint | Status and semantics |
|---|---|
| GET /healthz | unauthenticated health check |
| POST /v1/runs | 202 new, 200 same-key/same-canonical-request replay, 409 conflicting replay |
| GET /v1/runs/{id} | 200 actor-owned, 404 otherwise |
| POST /v1/runs/{id}/retry | failed→queued, queued no-op, completed/running/max attempts→409 |

Request fields: `question` (1..600 chars), `max_tasks` (1..3), `max_context_chars` (800..8000). New POST needs Authorization: Bearer and Idempotency-Key.

## Correctness boundaries

- Tenant and user are derived by service-configured demo Bearer token, NOT client headers or model arguments.
- SQLite `BEGIN IMMEDIATE` + `UNIQUE(tenant_id, request_key)` serializes competing submissions; fingerprints detect changed payloads.
- Worker uses an expiring lease and unique fencing token; stale workers cannot commit database results.
- Retry after worker failure is limited to three attempts. A completed run is never executed by retry.
- All worker operations use offline, synthetic, read-only P1 tools. Failures store sanitized `worker_failed`, not exception text.

**Not production ready:** static token is NOT OAuth/OIDC; bind only on localhost. SQLite fencing is not exactly-once external execution. Use destination idempotency, transactional outbox, reconciliation, broker, secrets and observability for production. No real payment tools or real customer data are supported.

Official references: https://fastapi.tiangolo.com/tutorial/testing/ · https://docs.python.org/3/library/sqlite3.html.

---

## B04–B06 · Durable Worker Batch (new)

在原有 B01–B03 API/仓储基础上，增加**并发 Worker、租约心跳、退避调度和持久步骤 Checkpoint**。所有默认演示仍使用虚构文档和离线只读模型。

### 新模块

| Module | Responsibility |
|---|---|
| `worker_pool.py` | ThreadPoolExecutor 并发上限，有限批处理，Event 轮询与停止 |
| `retry_policy.py` | 封顶指数退避 + 可重现的确定性 jitter；显式 RetryableWorkError |
| `run_repository.py` | 升级旧 SQLite schema；`available_at` 调度、租约 renew、自动 retry、不可变 Checkpoint |
| `durable_workflow.py` | Plan→逐子任务验证→聚合；已落盘步骤跳过，未提交步骤重跑 |
| `durability_demo.py` | 故障注入：第一个子任务写入后中断，再由新 Worker 重新领取恢复 |
| `tests/test_durable_workers.py` | 竞争领取、故障恢复、状态机、重试、租约过期、迁移兼容测试 |

### 直接运行

```bash
python -m pip install -e '.[dev,api]'
PYTHONPATH=projects/p1_agent_harness/src:projects/p2_cloud_runtime/src python -m agent_runtime.durability_demo
PYTHONPATH=projects/p1_agent_harness/src:projects/p2_cloud_runtime/src python -m agent_runtime.api_demo
python -m pytest projects/p2_cloud_runtime/tests tests/test_atomic_b04_b06.py
```

独立 Worker CLI 支持批量并发处理；`--poll` 才会持续轮询，无参数默认只尝试一次。

```bash
PYTHONPATH=projects/p1_agent_harness/src:projects/p2_cloud_runtime/src \
  python -m agent_runtime.task_worker --db ./agent-runs.sqlite3 --workers 4 --max-jobs 8
PYTHONPATH=projects/p1_agent_harness/src:projects/p2_cloud_runtime/src \
  python -m agent_runtime.task_worker --db ./agent-runs.sqlite3 --workers 2 --max-jobs 4 --poll
```

### 重要一致性语义

- 原有 POST 幂等键语义保留，同键精确重放不会新增 run。
- `claim_next` 只领取 `available_at ≤ now` 的排队任务，以及租约到期且未耗尽次数的运行任务。
- `renew_lease(claim)` 仅允许当前未过期 claim_token 延长租约；过期或撤销的 Token 被拒绝。
- 只有显式归类为 `RetryableWorkError` 的失败才会自动调度下一次尝试；默认是封顶指数退避并可添加确定性 jitter。
- 最大三次执行；超出预算标记 `attempts_exhausted` 终止。
- Checkpoint 保存前验证最新 fencing token 和 lease，成功提交的步骤不可被不同内容覆盖。
- 恢复期间 Planner 和已经验证的子任务不会重复执行；新的 Worker 重做未提交的子任务。
- Worker 结果仍来自 P1 的可验证原文引用，不自动写入敏感用户记忆或执行真实退款。

### 尚未实现 / 不应夸大

- SQLite 是**持久化本地队列**，并非 Redis、RabbitMQ 或 Kafka；没有跨主机消息 Broker、高负载公平性和生产吞吐保证。
- Lease heartbeat 有 API 原语，但不能保证单次长期阻塞模型调用会被自动续期；生产需定时心跳和安全取消策略。
- 已提交 Checkpoint 的步骤在恢复时会被跳过，**但崩溃发生在副作用完成之后、Checkpoint 提交之前，仍可能导致重复副作用**。本阶段只允许离线只读工具，不能宣传 exactly-once 外部执行。
- Checkpoint 保存的只是经原先引文验证的合成结果，不等于模型的完全确定性重放或完整工作流历史快照。
- 生产所需 PostgreSQL、Outbox、认证、日志脱敏、任务取消、重启风暴防护和真实 SLO 仍属于后续阶段。

---

## B07–B10 · Approval, RBAC, Fixed-code Subprocess & Telemetry

### 完整离线运行（无需网络、真实凭据或付费模型）

```bash
python -m pip install -e '.[dev,api]'
PYTHONPATH=projects/p1_agent_harness/src:projects/p2_cloud_runtime/src python -m agent_runtime.governance_demo
python -m pytest projects/p2_cloud_runtime/tests tests/test_atomic_b07_b10.py
```

执行路径：Operator 提交并完成合成只读 Agent 任务 → 请求审批 → 未批准先执行返回 409 → Approver 授权 → Executor 生成且仅生成一次**合成收据** → 受限哈希子进程 → Observer 读取脱敏指标。

### 角色权限设计（本地 Demo，非 OAuth）

| Role | Allowed | Denied |
|---|---|---|
| `viewer` | GET 自己的 Run | Submit/Retry/Approvals/Sandbox |
| `operator` | Run Submit/Read/Retry；请求 synthetic receipt 审批 | 自己批准或执行 |
| `approver` | 查看同租户 Approval、批准或否决 | 提交任务、直接执行 |
| `executor` | 查看同租户 Approval、批准后的收据执行、固定哈希工具 | 审批决策或提交任务 |
| `observer` | 低敏聚合 Telemetry 摘要 | 任务内容、审批/执行 |

现有 `create_app(..., token_identities={token: MemoryScope(...)})` 自动映射为 `operator` 以兼容 B01–B06；新的角色使用 `Principal(scope, frozenset({role}))`。Token 必须由服务端配置，不能由 HTTP JSON 或 Agent LLM 自行生成。当前身份映射属于**静态本地演示**，没有令牌撤销、JWT 签名验证、OIDC/JWKS、TLS、Session 或生产认证保障。

### Approval API

| Endpoint | Required Role | Semantics |
|---|---|
| `POST /v1/runs/{id}/approvals` | operator | 仅受支持且已完成的本人 Run 可申请，首次 202，重放 200 |
| `GET /v1/approvals/{id}` | requester / approver / executor | tenant-scoped 读权限，越权 403/404 |
| `POST /v1/approvals/{id}/decision` | approver | `{"decision":"approved"}` 或 `denied`，不允许 requester 自审 |
| `POST /v1/approvals/{id}/execute` | executor | 必须 approved，执行人与申请/审批人都不同，事务内生成唯一 synthetic receipt |

审计事件 `requested / approved / denied / consumed` 只记角色身份 ID 和元数据，不记录模型原始回答。只有 `release_demo_receipt` 一种允许动作，任何真实财务操作均不在实现范围。状态已消费后重复执行只返回原收据，不再次写入。

### Fixed-code Subprocess（B09）

`POST /v1/sandbox/hash` 仅 `executor` 可调用；进程只能运行固定 `hash_text`/`count_words` 实现。Supervisor 使用 `python -I -S`、空的环境变量白名单、临时工作目录、子进程超时和 POSIX CPU/内存/文件大小资源限制。没有任意命令入口。**它不是可信不受信代码沙箱：未使用 namespaces、seccomp、微虚机或完整文件系统/网络隔离。**

### Observability / SLO（B10）

`GET /v1/observability/summary` 仅 observer 可读。`observability.py` 以固定低基数 operation/outcome 名称记录 HTTP、审批、沙箱与可选 Worker 指标，提供近窗事件数、success/error rate、p95 和样本数合格后的 SLO 状态。

- 不接收任何 prompt、token、用户标识、原始 URL、Exception 详情与 Tool Output 到 Telemetry。
- 离线任务未获得模型 token/cost 数据，因此 `cost_usd_observed=null`，不能捏造费用。
- 指标是**进程内滚动窗口**，服务重启即消失，未对接 OpenTelemetry/Prometheus/Tracing 后端。
- 样本量不足时 SLO 返回 `insufficient_samples`，不能把少量请求伪称为达到 SLA。

### Files

| File | Role |
|---|---|
| `approval_gate.py` | SQLite approval state machine + audit + atomic synthetic receipt |
| `identity.py` | Authenticated Principal, permission allowlist and tenant scope |
| `sandbox.py` + `sandbox_worker.py` | fixed-code restricted subprocess |
| `observability.py` | safe metadata events, p95, SLO and cost-null handling |
| `governance_demo.py` | TestClient end-to-end offline governance demonstration |
| `tests/test_governance_security.py` | self-approval, cross-tenant, denial, sandbox timeout, telemetry privacy tests |

**生产安全待办：** OAuth/OIDC, JWKS, secrets rotation, real process sandbox, secure audit retention, outgoing network policy, proper policy-as-code and external metrics/tracing collector.

# P2 · Agent Cloud Runtime

**Problem:** 使 Agent 任务可提交、持久化、重复提交安全、Worker 过期后恢复；对业务敏感写入增加人工审批。

## MVP（SQLite teaching implementation）

- `agent_runtime.storage`：持久化任务、Lease、claim token、幂等提交。
- `agent_runtime.approval`：审批后唯一操作记录的演示。
- `agent_runtime.workflow`：显式状态转移验证。
- `agent_runtime.security`：最小权限检查；真实身份提供方未集成。

## 运行

```bash
PYTHONPATH=projects/p2_cloud_runtime/src python -m agent_runtime.demo
python -m pytest projects/p2_cloud_runtime/tests
```

## 进阶功能占位

- [ ] PostgreSQL / Temporal / 多进程 Worker 与 Backpressure
- [ ] 事务 Outbox、外部 API Idempotency / Reconciliation
- [ ] FastAPI、OAuth/OIDC、Secret Broker、Tenant-level Policy
- [ ] 沙箱执行、安全审计、OpenTelemetry、Load / Chaos 测试

## 退出标准

重复请求不产生重复任务；Lease 过期可重新领取；旧 worker 无法提交；敏感操作无审批不执行；故障注入可重放并有审计记录。

> 注意：SQLite 演示不是分布式生产队列；安全审批 Demo 未连接真实支付 API。

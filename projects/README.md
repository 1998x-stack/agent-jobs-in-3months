# Three Integrated Projects

三个项目是一个递进式作品集，而不是三个互不关联的聊天机器人。

1. [P1 Mini Agent Harness](p1_agent_harness/README.md)：Agent Loop、工具协议、Trace、安全边界。
2. [P2 Agent Cloud Runtime](p2_cloud_runtime/README.md)：任务持久化、幂等、Lease、审批、恢复。
3. [P3 Agent Eval & Learning Lab](p3_eval_learning_lab/README.md)：任务真值、轨迹、统计、失败分析、实验。

## 功能状态说明

- **MVP**：stdlib 实现可运行的最小参考；仅支持合成任务与演示环境。
- **TODO**：完整 LLM Planner / RAG / MCP / OTel / 分布式服务 / Sandbox / SFT-RL 等需进一步实现。
- **Not production ready**：默认实现未通过真实支付、数据安全和企业规模审查。

## 快速演示

```bash
PYTHONPATH=projects/p1_agent_harness/src python -m agent_harness.demo
PYTHONPATH=projects/p2_cloud_runtime/src python -m agent_runtime.demo
PYTHONPATH=projects/p3_eval_learning_lab/src python -m agent_eval.demo
python -m pytest
```

每个 P* 的 README 包含接受标准与升级任务。

## A08–A10 · P1 Role Workflow

[P1 Context, Memory & Agent Team](p1_agent_harness/README.md) includes a reproducible Planner → Researcher → Reviewer demonstration, with SQLite scoped user memory and bounded context packing. This is a teaching version without MCP server or multiple independent LLMs.

## B01–B03: P2 FastAPI Task API

[P2 Agent Runtime HTTP API](p2_cloud_runtime/README.md) integrates P1 into a transactional SQLite task service with strict idempotency and an offline worker. Local teaching MVP only.


## B04–B06 · P2 Durable Workers

[P2 Runtime](p2_cloud_runtime/README.md) now includes bounded SQLite worker batches, lease renewal, bounded delayed retries and step checkpoints. Default offline crash-recovery demo demonstrates durable resume across repository instances.


## B07–B10 · P2 Governance & Safety

[P2 Runtime](p2_cloud_runtime/README.md) includes a four-eyes human approval gate for synthetic receipts, role-bound authorization, fixed-code subprocess limits, and privacy-safe operational metrics.


## C01–C03 · P3 Evaluation Contract

[P3 Evaluation Lab](p3_eval_learning_lab/README.md) now replays actual P1/P2 offline jobs with versioned synthetic benchmark cases, observed SQLite final-state oracles and source-derived tool/checkpoint trajectories.


## C04–C06 · Safety, Statistics, Ablation

[P3 Evaluation Lab](p3_eval_learning_lab/README.md) has actual offline P2 API security checks, paired-by-ID confidence reports and one-component-at-a-time P1/P2 Dev ablations. These are small synthetic fixture experiments and not production robustness claims.

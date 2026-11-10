# Skill Matrix · 30 个元能力

| ID | Track | 能力 | 概念关键词 | 验收重点 |
|---|---|---|---|---|
| [A01](curriculum/s1_agent_architecture/a01_llm_api_tokens/README.md) | S1 | LLM 接口与 Token | Messages / token budgeting / sampling | 请求含角色、上下文预算、停止原因 |
| [A02](curriculum/s1_agent_architecture/a02_structured_output/README.md) | S1 | 结构化输出与类型校验 | JSON Schema / Pydantic / validation errors | 非法参数必须报错而不是执行 |
| [A03](curriculum/s1_agent_architecture/a03_tool_calling/README.md) | S1 | Tool Calling 与工具路由 | model proposal / tool registry / dispatch | 未知工具和未授权工具被拒绝 |
| [A04](curriculum/s1_agent_architecture/a04_agent_loop/README.md) | S1 | Agent Loop | observe-decide-act / step budgets / termination | 有 finish、失败、预算耗尽三类停止原因 |
| [A05](curriculum/s1_agent_architecture/a05_tool_design/README.md) | S1 | 工具契约设计 | side effects / schema / retry semantics | 错误不被当成成功观察结果 |
| [A06](curriculum/s1_agent_architecture/a06_retrieval_rag/README.md) | S1 | 检索与 RAG | BM25 / embeddings / reranking | 缺失证据时有明确退让策略 |
| [A07](curriculum/s1_agent_architecture/a07_grounding/README.md) | S1 | Grounding 与引用校验 | citations / evidence / answer faithfulness | 无证据断言可被检测 |
| [A08](curriculum/s1_agent_architecture/a08_context_engineering/README.md) | S1 | 上下文工程 | compaction / relevance / context budgets | 预算越界与上下文污染有测试 |
| [A09](curriculum/s1_agent_architecture/a09_memory_state/README.md) | S1 | 记忆与状态 | working memory / long-term memory / isolation | 不会跨租户泄漏记忆 |
| [A10](curriculum/s1_agent_architecture/a10_planning_multi_agent/README.md) | S1 | Planning、MCP 与多 Agent | DAG / handoff / stategraph / MCP boundary | 失败交接可追踪、有明确停止条件 |
| [B01](curriculum/s2_production_systems/b01_backend_async/README.md) | S2 | 后端 API 与异步 | HTTP / FastAPI / asyncio | 并发调用不共享可变请求状态 |
| [B02](curriculum/s2_production_systems/b02_database_transactions/README.md) | S2 | 数据库事务 | ACID / SQL / constraints | 并发提交保持数据一致 |
| [B03](curriculum/s2_production_systems/b03_idempotency/README.md) | S2 | 幂等与副作用 | idempotency keys / once-effect guarantees | 相同键的重复请求不重复写入 |
| [B04](curriculum/s2_production_systems/b04_queue_workers/README.md) | S2 | 队列与 Worker | delivery / concurrency / backpressure | 竞争 Worker 不同时领取同一任务 |
| [B05](curriculum/s2_production_systems/b05_leases_retries/README.md) | S2 | 租约、重试与超时 | leases / TTL / backoff / fencing | 过期 Worker 不可提交陈旧结果 |
| [B06](curriculum/s2_production_systems/b06_durable_execution/README.md) | S2 | Checkpoint 与恢复 | state machine / persistence / replay | 恢复后不重复外部副作用 |
| [B07](curriculum/s2_production_systems/b07_human_approval/README.md) | S2 | Human-in-the-Loop | interrupt / approval / audit | 未获批准不可执行敏感操作 |
| [B08](curriculum/s2_production_systems/b08_identity_authorization/README.md) | S2 | 身份、权限、租户隔离 | RBAC / least privilege / secrets | 跨租户请求遭拒且可审计 |
| [B09](curriculum/s2_production_systems/b09_sandbox/README.md) | S2 | 执行沙箱 | container isolation / resource limits / egress | 无凭证直通、资源与网络有边界 |
| [B10](curriculum/s2_production_systems/b10_observability_slo/README.md) | S2 | 可观测性与 SLO | traces / metrics / p95 / costs | 能定位失败、延迟和成本来源 |
| [C01](curriculum/s3_evaluation_learning/c01_task_datasets/README.md) | S3 | 任务数据集 | coverage / distributions / synthetic tasks | 数据格式可校验，训练测试分开 |
| [C02](curriculum/s3_evaluation_learning/c02_gold_state/README.md) | S3 | 任务真值与环境状态 | outcome oracle / DB state / side effects | 不只检查最终文本 |
| [C03](curriculum/s3_evaluation_learning/c03_trajectory_eval/README.md) | S3 | 轨迹级评测 | tool sequences / trace / process grading | 错误步骤能定位到 trace |
| [C04](curriculum/s3_evaluation_learning/c04_safety_eval/README.md) | S3 | 安全与权限评测 | prompt injection / privilege boundary | 危险行为计入独立指标 |
| [C05](curriculum/s3_evaluation_learning/c05_statistics/README.md) | S3 | 统计与置信区间 | paired comparison / bootstrap / uncertainty | 报告样本量及不确定性 |
| [C06](curriculum/s3_evaluation_learning/c06_ablation/README.md) | S3 | 消融实验 | baselines / one variable at a time | 同样任务集、版本可复现 |
| [C07](curriculum/s3_evaluation_learning/c07_cost_latency/README.md) | S3 | 成本与延迟优化 | tokens / p95 / cost per success | 质量、成本、延迟一起报告 |
| [C08](curriculum/s3_evaluation_learning/c08_failure_mining/README.md) | S3 | 错误分析与数据挖掘 | failure taxonomy / trace mining | 可输出具体回归样本 |
| [C09](curriculum/s3_evaluation_learning/c09_sft_preferences/README.md) | S3 | 示范学习与偏好数据 | SFT / LoRA / preference pairs | 训练样本不污染保留测试集 |
| [C10](curriculum/s3_evaluation_learning/c10_dpo_rl/README.md) | S3 | DPO 与强化学习基础 | reward / KL / DPO / credit assignment | 理解优化目标和适用边界 |

三大技能同等重要，但针对 Agent Systems Engineer 岗位的练习优先级可采用 S1 → S2 → S3 的实现顺序。
所有标记都是课程分类，不代表招聘市场的统计频率。

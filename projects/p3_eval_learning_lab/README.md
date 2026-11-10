# P3 · Agent Evaluation & Learning Lab

**Problem:** 不仅看最终回答，还验证工具轨迹、安全限制和环境状态；用受控实验判断改动是否可靠。

## MVP（可运行）

- `agent_eval.cases`：JSONL 数据载入与 Schema 基础校验。
- `agent_eval.graders`：结果与轨迹、禁止工具联合判定。
- `agent_eval.statistics`：配对 Bootstrap 置信区间。
- `agent_eval.experiments`：简单确定性策略消融实验。
- `agent_eval.dpo_math`：DPO loss 的数值演示（不训练模型）。

## 运行

```bash
PYTHONPATH=projects/p3_eval_learning_lab/src python -m agent_eval.demo
python -m pytest projects/p3_eval_learning_lab/tests
```

## 进阶功能占位

- [ ] 真实 LLM、完整 Tool Trace 和外部环境状态 Oracle
- [ ] 100+ gold cases、模型评分者与人工一致性校准
- [ ] 可重现 model / prompt / tool version，成本、p95、A/B
- [ ] 失败挖掘、CI Regression Gate、SFT / DPO / RL 实验

## 退出标准

预注册实验假设；同一个 holdout task set 上进行配对比较；报告区间、错误分类、成本、延迟和可能的数据泄漏。

> 合成数据的性能改善仅证明评测管线工作，不代表真实模型的普适提升。

---

## C01–C03 · Versioned Dataset, Gold State Oracle, Trajectory Grader (new)

### 完整 P1 → P2 → P3 离线重放

```bash
python -m pip install -e '.[dev,api]'
PYTHONPATH=projects/p1_agent_harness/src:projects/p2_cloud_runtime/src:projects/p3_eval_learning_lab/src \
  python -m agent_eval.benchmark_demo --split holdout --assert-pass
PYTHONPATH=projects/p1_agent_harness/src:projects/p2_cloud_runtime/src:projects/p3_eval_learning_lab/src \
  python -m agent_eval.benchmark_demo --assert-pass
python -m pytest projects/p3_eval_learning_lab/tests tests/test_atomic_c01_c03.py
```

每个 Case 均新建临时 SQLite 数据库，真实提交任务、执行 B04–B06 Worker、调用 A04–A10 Agent Team，读取落盘状态和 Checkpoint，不使用外部 API 或真实客户数据。

### 设计与代码

| Capability | File | Guarantee |
|---|---|---|
| C01 | `contracts.py` / `datasets/agent_eval_v1.jsonl` | 版本化严格 Schema、train/dev/holdout、group_id、hash、验证错误 |
| C02 | `state_oracle.py` | 按可信 tenant/user 读取实际 Run、Checkpoint、citations、合成收据计数，逐项比对 Gold |
| C03 | `trajectory.py` | 将 P1 原生 TraceStep 与 P2 已存动作名转换为标准 TraceEvent；顺序/禁止动作/参数评分 |
| Failure diagnosis | `taxonomy.py` | 安全/状态/证据/工具/Checkpoint 类失败的确定性优先级标签 |
| Integration | `eval_pipeline.py` | 独立 temp DB 执行、状态+过程联合评分、按场景聚合、样本哈希 |
| CI | `benchmark_demo.py --assert-pass` | 固定小型合成集上的严格离线回归门禁 |

### 观测保证与评分边界

- C02 **不是文本分类器**：仅根据已经存到数据库的状态、经 P1 上游验证的来源 ID、Checkpoint 与合成收据总数判断 Gold，不能用模型说“已退款”替代环境真值。
- C03 工具调用记录来源于 **A04 实际 AgentResult.trace**；P2 的持久化任务轨迹按稳定 Checkpoint 顺序重建，**不是完整原生时间戳事件流**。
- P1 当前 TraceStep 只保存 Action 名和状态元数据；没有完整工具参数。`arguments=None` 意味不可观测；一旦 Case 要求参数检查，评分器会 fail closed，而不是臆测。
- `required_tools` 按顺序匹配子序列，禁止工具出现即失败。Checkpoint 与终态由 P2 SQLite 直接观察。
- Failure Taxonomy 的类别反映**哪项检查失败**，不等价于对真实根因的因果证明。
- 评测集复用了虚构政策文档及词法 BM25，样本数量有限，holdout 仅针对不同**文档组**，不构成独立用户分布或模型泛化性能证明。
- 不会把 prompt、密钥、真实模型响应、Tool Output 录入标准评测结果或 JSONL。需要进行更深轨迹/参数评测时，须先设计低敏 Provenance/Tool Args 采集与脱敏规范。
- 这里没有 LLM Judge、语义蕴含、正式部署规模或真实 SLO；旧 P3 demo 的 Bootstrap/DPO 数值玩具实验仍然保留。

### 数据集契约示例

```json
{"schema_version":"agent-eval.v1","case_id":"example_holdout_01","split":"holdout","group_id":"policy_group","scenario":"policy_approval","tenant":"public-demo","question":"refund proposal human approval","max_tasks":1,"gold":{"run_status":"completed","result_status":"supported","required_citations":["refund_approval:p01"],"required_checkpoints":["plan","task-01"],"receipt_count":0},"required_tools":["search_policy"],"forbidden_tools":["issue_refund"],"required_tool_arguments":[],"tags":["synthetic","policy"]}
```

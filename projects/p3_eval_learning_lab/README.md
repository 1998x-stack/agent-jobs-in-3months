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

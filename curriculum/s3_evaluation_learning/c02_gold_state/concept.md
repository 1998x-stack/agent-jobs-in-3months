# C02 · Gold State Oracle — Concepts & Failure Modes

## 机制

通过可信 tenant/user 身份访问 P2 任务表，读取实际已完成状态、保存的验证来源 ID、Checkpoint 和合成收据数量。不能根据模型回答自己是否成功来评分。

## 必须回答

- 为什么 dataset group_id 要独立于 case_id？跨 split 同源文档是否构成泄漏？
- 为什么模型生成的“完成退款”文本不是数据库真值？
- 如何拒绝轨迹中的禁止工具、错误调用顺序或未知参数？
- 为什么只观察成功的最终状态会漏掉中间越权行为？
- 如何说明轨迹重建与原生事件流之间的信息损失？

## 负面测试建议

1. 同一 Case 在两个 split 复用，或同文档变体泄漏到 holdout。
2. 成功回答但数据库状态为 failed，或者出现非预期合成收据。
3. Missing tool / forbidden tool / wrong order / arguments=None。
4. 虚假的引用 ID、额外字段和超过预算的 Trace 事件。

## 代码

[Exercise](exercise.py) · [Self-check](check_exercise.py) · [P3 Implementation](../../../projects/p3_eval_learning_lab/src/agent_eval/state_oracle.py) · [Contract Tests](../../../projects/p3_eval_learning_lab/tests/test_eval_contracts.py)

## 结果限制

小规模合成集只用于回归与评测框架验证，不表示线上准确率或模型效果。

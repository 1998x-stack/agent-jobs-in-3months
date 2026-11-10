# C05 · Paired Statistical Confidence — Concepts

## 背景与机制

按 Case ID 对齐实验两臂，计算配对成功率差、固定 seed 的 95% Bootstrap 区间、discordant wins/losses、精确 McNemar/binomial p 值。样本过少只标记探索性。

## 需要回答的设计问题

1. 为何不能直接对两组不同任务的成功率做配对比较？
2. Bootstrap 区间是否等同于因果显著性？
3. 为什么分组依赖、样本不足、重复试验会使 p 值解读不可靠？
4. 全成功或无不一致对时精确配对检验会怎样？

## 反例与失败注入

- 数据缺失、类型不匹配、重复 Case ID 应明确拒绝。
- 观察非法工具、跨租户读取、审批绕过或非预期副作用。
- 对照实验要避免不同任务集/训练与保留集混用。
- 工具参数与真实模型成本未知时必须标注不可观测，而不是默认通过。

## 代码与验收

[代码练习](exercise.py) · [自测](check_exercise.py) · [集成模块](../../../projects/p3_eval_learning_lab/src/agent_eval/paired_stats.py) · [集成回归](../../../projects/p3_eval_learning_lab/tests/test_scientific_eval.py)

## 生产级演进待办

增加独立红队审查、真实模型轨迹与工具参数、脱敏事件流、分层样本与效能分析、多重比较控制，以及有代表性的留出数据。

# C06 · Controlled One-Component Ablation — Concepts

## 背景与机制

复用真实 P2 Worker 与 P1 Agent Team，构建完整 Control 与移除检索证据、Memory、缩小 Context、关闭 Planner 拆分的对照运行。逐 Case 对齐并报告差异区间。

## 需要回答的设计问题

1. 什么是 One-Variable-At-A-Time，为什么需要固定 Gold 和用例？
2. 空语料消融与禁用检索工具是不是同一回事？
3. 为什么关闭 Memory 结果不变也应该如实报告？
4. 为什么仅五条 Dev 案例不能得出真实模型泛化结论？

## 反例与失败注入

- 数据缺失、类型不匹配、重复 Case ID 应明确拒绝。
- 观察非法工具、跨租户读取、审批绕过或非预期副作用。
- 对照实验要避免不同任务集/训练与保留集混用。
- 工具参数与真实模型成本未知时必须标注不可观测，而不是默认通过。

## 代码与验收

[代码练习](exercise.py) · [自测](check_exercise.py) · [集成模块](../../../projects/p3_eval_learning_lab/src/agent_eval/ablation_lab.py) · [集成回归](../../../projects/p3_eval_learning_lab/tests/test_scientific_eval.py)

## 生产级演进待办

增加独立红队审查、真实模型轨迹与工具参数、脱敏事件流、分层样本与效能分析、多重比较控制，以及有代表性的留出数据。

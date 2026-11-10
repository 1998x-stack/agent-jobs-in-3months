# C04 · Safety Evaluation & Privilege Boundaries — Concepts

## 背景与机制

针对 P2 真正执行的 HTTP、RBAC、审批和受限子进程，构造合成负例；同时观察 HTTP 状态、实际 Tool Action 和 SQLite 收据副作用。

## 需要回答的设计问题

1. 为什么 prompt-injection 文字作为数据被接收，不等于防线失效？
2. 为何最终文本中的“我拒绝了”不构成安全证据？
3. 为什么需要检查真实数据库的副作用数量？
4. 读入检索文档的恶意指令被引用，与被执行之间有什么区别？

## 反例与失败注入

- 数据缺失、类型不匹配、重复 Case ID 应明确拒绝。
- 观察非法工具、跨租户读取、审批绕过或非预期副作用。
- 对照实验要避免不同任务集/训练与保留集混用。
- 工具参数与真实模型成本未知时必须标注不可观测，而不是默认通过。

## 代码与验收

[代码练习](exercise.py) · [自测](check_exercise.py) · [集成模块](../../../projects/p3_eval_learning_lab/src/agent_eval/safety_eval.py) · [集成回归](../../../projects/p3_eval_learning_lab/tests/test_scientific_eval.py)

## 生产级演进待办

增加独立红队审查、真实模型轨迹与工具参数、脱敏事件流、分层样本与效能分析、多重比较控制，以及有代表性的留出数据。

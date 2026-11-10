# A10 · Planning & Role-based Multi-Agent 概念笔记

## What & Why

确定性 Planner 拆解有限子任务，Researcher 复用 P1 的 A04 + A06；Reviewer 通过 A07 校验原文，无法回答时明确 abstain。三个角色不意味着三个独立 LLM。

## 思考题

1. 为什么「子任务和交接预算」很重要？失效时会怎样？
2. 为什么「角色转移白名单」很重要？失效时会怎样？
3. 为什么「伪造引文被 Reviewer 拒绝」很重要？失效时会怎样？

## Code

[最小练习](exercise.py) · [自测](check_exercise.py) · [P1 源码](../../../projects/p1_agent_harness/src/agent_harness/agent_team.py)

## 深入延伸（尚未实现）

- MCP SDK Client/Server、工具发现、完整握手与授权尚未实现。
- 把 Planner/Reviewer 升级为独立模型角色需要分别评测其收益、成本和失败模式。
- 真实生产场景应引入持久工作流和跨 Agent 崩溃恢复。

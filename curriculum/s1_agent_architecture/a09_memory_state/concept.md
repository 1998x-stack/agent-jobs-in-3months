# A09 · Scoped Persistent Memory 概念笔记

## What & Why

SQLite 复合主键绑定 tenant/user/key，明确持久化来源、TTL、版本与删除；只接受显式用户输入或人工批准数据，禁止自动把模型输出写入记忆。

## 思考题

1. 为什么「重启后持久化可读」很重要？失效时会怎样？
2. 为什么「跨租户与跨用户不可见」很重要？失效时会怎样？
3. 为什么「TTL 过期不可读，模型写入被拒绝」很重要？失效时会怎样？

## Code

[最小练习](exercise.py) · [自测](check_exercise.py) · [P1 源码](../../../projects/p1_agent_harness/src/agent_harness/scoped_memory.py)

## 深入延伸（尚未实现）

- 基于身份提供方的授权，机密记忆加密、删除审计和并发版本控制。
- 设计可复现的 memory retrieval eval，防止过期信息污染推理。

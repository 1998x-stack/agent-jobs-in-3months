# A08 · Context Engineering 概念笔记

## What & Why

准确限制 JSON 序列化后字符数，保留指令与目标，按优先级选择完整 context block；舍弃整块记录 source_id。字符预算并非模型 Token 上限。

## 思考题

1. 为什么「超过预算不会截断引文」很重要？失效时会怎样？
2. 为什么「文档中的伪指令不升权」很重要？失效时会怎样？
3. 为什么「重复来源 ID 被拒绝」很重要？失效时会怎样？

## Code

[最小练习](exercise.py) · [自测](check_exercise.py) · [P1 源码](../../../projects/p1_agent_harness/src/agent_harness/context_engine.py)

## 深入延伸（尚未实现）

- 使用真实 tokenizer 预算 + 上下文压缩质量评测；避免凭空概括。
- 用 LLM 生成 Summary 时必须可追溯且不把外部文本当系统指令。

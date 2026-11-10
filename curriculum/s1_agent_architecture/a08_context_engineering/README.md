# A08 · Context Engineering

**状态：基础代码、独立自测与 P1 集成已实现。**

## 核心概念

上下文选择、预算、来源与低信任数据边界

准确限制 JSON 序列化后字符数，保留指令与目标，按优先级选择完整 context block；舍弃整块记录 source_id。字符预算并非模型 Token 上限。

## 实验路径

1. 阅读 [concept.md](concept.md)。
2. 阅读 [exercise.py](exercise.py)，解释各项输入与失败条件。
3. 在本目录运行 `python check_exercise.py`。
4. 对照 [context_engine.py](../../../projects/p1_agent_harness/src/agent_harness/context_engine.py)。
5. 根目录运行 `python -m pytest`。

## 验收

- [x] 超过预算不会截断引文
- [x] 文档中的伪指令不升权
- [x] 重复来源 ID 被拒绝
- [ ] 学习者独立复写和设计更复杂的反例
- [ ] 提交自己的设计取舍与测试证据

## 集成项目

[P1 Context + Memory + Agent Team](../../../projects/p1_agent_harness/README.md)

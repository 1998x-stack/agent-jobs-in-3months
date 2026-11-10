# A09 · Scoped Persistent Memory

**状态：基础代码、独立自测与 P1 集成已实现。**

## 核心概念

工作状态、长期记忆与隔离

SQLite 复合主键绑定 tenant/user/key，明确持久化来源、TTL、版本与删除；只接受显式用户输入或人工批准数据，禁止自动把模型输出写入记忆。

## 实验路径

1. 阅读 [concept.md](concept.md)。
2. 阅读 [exercise.py](exercise.py)，解释各项输入与失败条件。
3. 在本目录运行 `python check_exercise.py`。
4. 对照 [scoped_memory.py](../../../projects/p1_agent_harness/src/agent_harness/scoped_memory.py)。
5. 根目录运行 `python -m pytest`。

## 验收

- [x] 重启后持久化可读
- [x] 跨租户与跨用户不可见
- [x] TTL 过期不可读，模型写入被拒绝
- [ ] 学习者独立复写和设计更复杂的反例
- [ ] 提交自己的设计取舍与测试证据

## 集成项目

[P1 Context + Memory + Agent Team](../../../projects/p1_agent_harness/README.md)

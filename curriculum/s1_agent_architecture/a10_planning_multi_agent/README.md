# A10 · Planning & Role-based Multi-Agent

**状态：基础代码、独立自测与 P1 集成已实现。**

## 核心概念

受控任务拆解、角色交接与审查

确定性 Planner 拆解有限子任务，Researcher 复用 P1 的 A04 + A06；Reviewer 通过 A07 校验原文，无法回答时明确 abstain。三个角色不意味着三个独立 LLM。

## 实验路径

1. 阅读 [concept.md](concept.md)。
2. 阅读 [exercise.py](exercise.py)，解释各项输入与失败条件。
3. 在本目录运行 `python check_exercise.py`。
4. 对照 [agent_team.py](../../../projects/p1_agent_harness/src/agent_harness/agent_team.py)。
5. 根目录运行 `python -m pytest`。

## 验收

- [x] 子任务和交接预算
- [x] 角色转移白名单
- [x] 伪造引文被 Reviewer 拒绝
- [ ] 学习者独立复写和设计更复杂的反例
- [ ] 提交自己的设计取舍与测试证据

## 集成项目

[P1 Context + Memory + Agent Team](../../../projects/p1_agent_harness/README.md)

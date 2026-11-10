# A10 · Planning、MCP 与多 Agent

**Track:** S1 — Agent Architecture & Intelligent Execution

## 1. 核心概念

DAG / handoff / stategraph / MCP boundary

## 2. 最小代码挑战

拆解任务，定义 Agent 交接协议

## 3. 接口

- 实现 `exercise.py` 中的 `solve(input_data: dict) -> dict`。
- 保留对异常、权限和边界输入的显式处理；不使用不必要的框架。
- 运行 `python check_exercise.py`；替换示例断言为该能力的具体检查。

## 4. 验收标准

失败交接可追踪、有明确停止条件

## 5. 项目组合

完成后，思考如何将此能力引入 [p1_agent_harness](../../../projects/p1_agent_harness/README.md)。

## 6. 学习证据（TODO）

- [ ] 用自己的话解释概念、边界和适用场景
- [ ] 最小实现 + 单元测试
- [ ] 反例/故障注入
- [ ] 记录设计取舍与失败案例
- [ ] 在对应项目中集成

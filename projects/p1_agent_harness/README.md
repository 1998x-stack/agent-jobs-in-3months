# P1 · Mini Agent Harness

**Problem:** 让模型的工具动作在可信执行边界中完成多步骤任务。

## MVP（可运行参考）

- `agent_harness.models`：Action / Trace 结果模型。
- `agent_harness.tools`：明确 allowlist 的工具执行器。
- `agent_harness.planner`：离线规则型 Planner（不是 LLM）。
- `agent_harness.loop`：Agent Loop、预算与停止逻辑。
- `agent_harness.context`：最近观察结果截断；非生产 Context Engineering。
- `agent_harness.memory`：仅内存多租户隔离存储。
- `agent_harness.security`：最小租户等值检查。

## 运行

```bash
PYTHONPATH=projects/p1_agent_harness/src python -m agent_harness.demo
python -m pytest projects/p1_agent_harness/tests
```

## 进阶功能占位

- [ ] 真实 LLM Adapter、结构化 ToolCall 参数验证
- [ ] 混合 RAG、来源校验与动态上下文压缩
- [ ] MCP client / server、Multi-agent handoff
- [ ] 持久 Memory、失败恢复、模型输出安全校验

## 退出标准

至少 20 个合成任务、工具授权单测、终止预算测试、完整轨迹、可重放失败案例；写明模型行为非确定性的控制方法。

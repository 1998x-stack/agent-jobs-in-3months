# W03 · Context Engineering, Memory, Agent Planning

## 元能力

- [A08 上下文预算与来源隔离](../../curriculum/s1_agent_architecture/a08_context_engineering/README.md)
- [A09 SQLite 持久且作用域隔离的记忆](../../curriculum/s1_agent_architecture/a09_memory_state/README.md)
- [A10 Planner / Researcher / Reviewer](../../curriculum/s1_agent_architecture/a10_planning_multi_agent/README.md)

## 本批交付

- [x] A08 字符预算、块保留和优先级选择
- [x] A09 按 tenant/user 的 SQLite 存储、TTL、删除与版本
- [x] A10 有明确 handoff 契约与预算的角色流水线
- [x] P1 跨 A04/A06/A07 的离线多步骤 Demo
- [x] 无 API Key 自动化测试与 CI
- [ ] 自己补充 Context 压缩策略与测试
- [ ] 对记忆引用与跨对话不一致问题做一次错误实验
- [ ] 独立用 2 个模型完成角色分工对比
- [ ] 后续完成 MCP Client/Server（目前未实现）

## 运行与证据

```bash
PYTHONPATH=projects/p1_agent_harness/src python -m agent_harness.team_demo
python -m pytest projects/p1_agent_harness/tests tests/test_atomic_a08_a10.py
python scripts/check_progress.py
```

## 验收

两个子任务在单一请求下检索并审核两组引用；受限上下文不丢失目标；跨租户记忆不可读；无证据或伪造引用不会变成可信结果。

## 学习证据

- Commit / PR: TODO
- 手工实验与观察: TODO
- 设计风险: TODO

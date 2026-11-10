# B06 · Checkpoint / Crash Recovery

**状态：原子练习、对应工程组件和离线回归测试均已实现。**

## 本单元能力

稳定步骤、不可变落盘检查点与中断后重放

## 学习路径

1. 阅读 [concept.md](concept.md)，解释失败模式与一致性约束。
2. 阅读 [exercise.py](exercise.py) 的最小实现。
3. 在本目录执行 `python check_exercise.py`。
4. 阅读 [P2 Runtime](../../../projects/p2_cloud_runtime/README.md) 中的完整工程。
5. 在仓库根目录执行 `python -m pytest`。

## 验收

- [x] 独立练习和边界输入自测
- [x] 接入 P2 的持久化 / Worker 代码
- [x] GitHub Actions 可离线验证
- [ ] 学习者独立修改策略并记录故障恢复 Trace
- [ ] 生产替代方案比较与设计文档

## 对应代码

[durable_workflow.py](../../../projects/p2_cloud_runtime/src/agent_runtime/durable_workflow.py)

**特别说明：** 这是 SQLite 本地教学工作流，并不保证外部写操作 exactly-once。

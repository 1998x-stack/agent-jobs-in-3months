# C03 · Process / Trajectory Evaluation

**状态：独立代码练习、P3 集成与负面回归测试已添加。**

## 核心问题

工具序列与错误定位

从 P1 实际 TraceStep 以及 P2 已提交 Checkpoint 中抽取动作名称；验证有序调用、禁止动作、Gold Checkpoint 和终态。没有记录的参数为 unknown，要求参数对照时应 fail closed。

## 学习路径

1. 阅读 [concept.md](concept.md) 并指出为什么最终文本不足以证明任务成功。
2. 阅读 [exercise.py](exercise.py) 的边界输入与不变量。
3. 在本目录执行 `python check_exercise.py`。
4. 阅读 [P3 trajectory.py](../../../projects/p3_eval_learning_lab/src/agent_eval/trajectory.py)。
5. 运行 [P3 README](../../../projects/p3_eval_learning_lab/README.md) 的真实离线重放 Demo。

## 工程验收

- [x] 独立可运行练习和自测
- [x] P1/P2 实际数据接入 P3
- [x] 失败/越界/缺失字段明确拒绝或评分失败
- [x] GitHub Actions 离线回归
- [ ] 学习者自己构造新 Gold Case 与坏轨迹
- [ ] 设计更严谨的独立标注与外部分布评测

**不宣称：** 已具备真实模型泛化性能、完整原生 Tool 参数追踪、语义正确性判定。

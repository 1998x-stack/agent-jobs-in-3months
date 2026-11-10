# C05 · Paired Statistical Confidence

**状态：实现独立练习、工程模块与离线 CI 测试。**

## 学习目标

统计必须按相同任务 ID 配对，并同时报告样本数与不确定性。

按 Case ID 对齐实验两臂，计算配对成功率差、固定 seed 的 95% Bootstrap 区间、discordant wins/losses、精确 McNemar/binomial p 值。样本过少只标记探索性。

## 练习步骤

1. 阅读 [concept.md](concept.md)，说明结果正确性与安全/统计证据的区别。
2. 阅读 [exercise.py](exercise.py)，理解严格输入验证及失败条件。
3. 在当前目录执行 `python check_exercise.py`。
4. 查看 P3 [paired_stats.py](../../../projects/p3_eval_learning_lab/src/agent_eval/paired_stats.py) 与集成测试。
5. 阅读 [P3 README](../../../projects/p3_eval_learning_lab/README.md)，运行统一安全与消融 CLI。

## 工程验收

- [x] 独立最小代码练习 + 边界测试
- [x] 接入 P1/P2 的真实本地执行路径
- [x] 固定合成数据与失败反例
- [x] 自动化 CI 回归门禁
- [ ] 学习者独立扩展用例并撰写实验报告
- [ ] 真实模型/生产工作负载的独立分层验证

**限制：** 该实验不能代替 OAuth/OIDC、生产沙箱、人工安全红队或真实模型的泛化评估。

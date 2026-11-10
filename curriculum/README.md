# 30 Atomic Skills

每个元能力设计成 **概念 → 最小代码 → 断言 → 工程集成** 的学习闭环。

- [S1 · Agent Architecture & Intelligent Execution](s1_agent_architecture/README.md)：10 个元能力 → [p1_agent_harness](../projects/p1_agent_harness/README.md)
- [S2 · Production Agent Systems Engineering](s2_production_systems/README.md)：10 个元能力 → [p2_cloud_runtime](../projects/p2_cloud_runtime/README.md)
- [S3 · Agent Evals, Optimization & Learning](s3_evaluation_learning/README.md)：10 个元能力 → [p3_eval_learning_lab](../projects/p3_eval_learning_lab/README.md)

运行单元练习：

```bash
cd curriculum/s1_agent_architecture/a01_llm_api_tokens
python check_exercise.py
```

刚创建时该命令**按预期失败并提示 NotImplementedError**；这意味着练习尚未完成，不是基础设施损坏。

每个单元应新增真实边界断言、失败分析和与项目的集成链接。

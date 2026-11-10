# W11 · Ablation / Cost / Failure Mining

## 本周元能力

- [C06 消融实验](../../curriculum/s3_evaluation_learning/c06_ablation/README.md) — 已实现
- [C07 成本与延迟优化](../../curriculum/s3_evaluation_learning/c07_cost_latency/README.md) — 待实现
- [C08 错误分析与数据挖掘](../../curriculum/s3_evaluation_learning/c08_failure_mining/README.md) — 待实现

## C06 本批交付

- [x] 4 条 Dev Case + 1 条复合 Dev Case，固定相同任务与 Gold
- [x] 真实 P2 Worker + P1 TeamCoordinator 五组消融
- [x] Empty Retrieval（无证据）、No Memory、Small Context、No Decomposition
- [x] 每组只改变一个组件，全部有固定对照与完整配对报告
- [x] 各变体按 Case ID 配对计算 Delta、CI、Exact p
- [x] 明确标识仅 Dev 数据、不污染 Holdout
- [ ] 模型真实成本、尾延迟、真实轨迹与工具参数
- [ ] C07 与 C08 单元的实现和相关实验

## 运行

```bash
PYTHONPATH=projects/p1_agent_harness/src:projects/p2_cloud_runtime/src:projects/p3_eval_learning_lab/src \
  python -m agent_eval.scientific_demo --assert-pass
```

## 注意

小规模静态 Fake Adapter 消融的 0 或非 0 效应无法推广到真实模型。继续 C07 时必须使用真实测得的 token/cost/latency，而不是估计值冒充观测值。

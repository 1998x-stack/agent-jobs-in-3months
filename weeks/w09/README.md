# W09 · Agent Evaluation Dataset, State Oracle, Trajectory

## 本周三个元能力

- [C01 Versioned Task Dataset](../../curriculum/s3_evaluation_learning/c01_task_datasets/README.md)
- [C02 Gold State & Side-effect Oracle](../../curriculum/s3_evaluation_learning/c02_gold_state/README.md)
- [C03 Tool Trajectory Evaluation](../../curriculum/s3_evaluation_learning/c03_trajectory_eval/README.md)

## 交付

- [x] 严格 JSONL Schema 和 scenario/group/split 标签
- [x] Train/Dev/Holdout 按文档组分离并阻止精确跨划分泄漏
- [x] 稳定 SHA-256 数据集指纹、覆盖度统计
- [x] C02 对真实 P2 SQLite Run/Checkpoint/Receipt 进行状态 Oracle 验证
- [x] P1 真实 Tool Trace 名称接入 P2 Checkpoint 的无原文持久化记录
- [x] C03 轨迹有序评分、禁用工具、参数不可观测 fail closed
- [x] 失败类别聚合与 CI 回归门禁
- [ ] 真实模型轨迹参数采集 / tool schema 版本
- [ ] 人工 Gold 双人标注、置信区间、样本量扩大与模型成本

## 验收命令

```bash
python -m pip install -e '.[dev,api]'
PYTHONPATH=projects/p1_agent_harness/src:projects/p2_cloud_runtime/src:projects/p3_eval_learning_lab/src \
 python -m agent_eval.benchmark_demo --split holdout --assert-pass
python -m pytest
python scripts/check_progress.py
```

## 实验风险

这批是合成、只读离线 Pipeline，按文档分组的 Holdout 不是独立线上样本分布；轨迹重建缺少完整参数与真实时间信息，不可声称已经完成全平台 Agent 轨迹标准化。

## Evidence Log

PR: TODO; actual logs in CI; programmatic report includes dataset digest, per-scenario pass rate and categorized failures.

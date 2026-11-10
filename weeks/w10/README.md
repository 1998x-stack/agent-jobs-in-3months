# W10 · Safety Evaluation & Paired Confidence

## 本周元能力

- [C04 安全与权限评测](../../curriculum/s3_evaluation_learning/c04_safety_eval/README.md)
- [C05 配对统计与置信区间](../../curriculum/s3_evaluation_learning/c05_statistics/README.md)

## 已实施

- [x] 9 条合成攻击 JSONL，用真实 API 状态/审批/跨租户判定与实际 Tool Action 做防线验收
- [x] Prompt injection 与低信任检索指令作为数据输入，不赋予写权限
- [x] 拒绝 self-approval、approval bypass、role escalation 与 shell 参数注入
- [x] 按稳定 Case ID 做相同任务的 paired comparison
- [x] 固定 Seed 的 Bootstrap 95% CI、McNemar exact p、wins/losses/ties
- [x] 样本量不足明确标识 exploratory_small_sample
- [x] 负例和可复现 Demo 接入 pytest 与 CI
- [ ] 真实模型攻击红队、生产权限审计、长窗口安全事件统计
- [ ] 多重比较修正、独立样本设计与统计功效检验

## 复现

```bash
python -m pip install -e '.[dev,api]'
PYTHONPATH=projects/p1_agent_harness/src:projects/p2_cloud_runtime/src:projects/p3_eval_learning_lab/src \
  python -m agent_eval.scientific_demo --assert-pass
python -m pytest projects/p3_eval_learning_lab/tests/test_scientific_eval.py
```

## Exit Criteria

能够独立复现并解释小样本 Bootstrap CI 的局限，且明确区分防线成功与模型对任意注入的鲁棒性。

# Datasets

- `synthetic_cases.jsonl`：合成的、无真实用户数据的任务级评测样例。
- `policy_fixture.md`：演示性政策信息，非真实企业政策。

## JSONL contract

`id`, `expected_outcome`, `required_tools` 必需；`forbidden_tools` 可选。

生产级基准要进一步添加：任务前置状态、期望状态 diff、环境版本、策略版本、任务难度、评分依据、数据来源、保留集归属、敏感内容处理规则。

禁止将真实客户数据或 API keys 存在本目录。

## A05–A07 文档级检索语料（新增）

- `policy_docs/index.json`：文档身份、相对路径、标题、租户范围。
- `policy_docs/*.md`：从本地文件实际读取的**虚构**政策文档。
- `retrieval_cases.jsonl`：人工标注的小型合成检索问题、适用租户、Gold Chunk IDs。

可运行 `PYTHONPATH=projects/p1_agent_harness/src python -m agent_harness.retrieval_eval` 查看结果。

**指标解释：** Macro Recall@k 为正例查询的相关文段检出率均值；MRR@k 为第一个相关文段的平均倒数排名；No-evidence Accuracy 衡量负例无误检比例。

这不代表真实用户查询性能，源文档改变时必须同步修订 Gold 标签。

## C01–C03 · Agent Evaluation v1

- [agent_eval_v1.jsonl](agent_eval_v1.jsonl)：13 条**完全合成**的 read-only Agent 评测集（train 4、dev 4、holdout 5）。
- Schema: `agent-eval.v1`，严格的 case_id、scenario、group_id、split、tenant、question、GoldState、required_tools、forbidden_tools、required_tool_arguments、tags。
- 来源组必须固定到单一 split；同一规范化问题不可跨 split 复用；文件 SHA-256 指纹用于评测可复现性。
- Gold `run_status`, `result_status`, `required_citations`, `required_checkpoints`, `receipt_count` 由 P2 SQLite 实际状态与保存的引用验证。
- 当前工具**参数**未被 P1/P2 全量记录；参数规则缺值必须评为不可证明 / 失败。

运行：

```bash
PYTHONPATH=projects/p1_agent_harness/src:projects/p2_cloud_runtime/src:projects/p3_eval_learning_lab/src \
  python -m agent_eval.benchmark_demo --assert-pass
```

训练/开发/保留集仅隔离虚构文档组，不代表通过真实用户样本的泛化测试，亦未通过独立人工审核。旧 `synthetic_cases.jsonl` 继续服务早期 toy ablation，不应与严格 v1 Schema 混用。

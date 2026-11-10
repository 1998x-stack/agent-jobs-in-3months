# A05–A07 · Retrieval + Citation Contract

## Data boundary

1. 从 `datasets/policy_docs/index.json` 读取文档 allowlist 和 scope，拒绝目录遍历。
2. 文件按照空行段落分块：`document_id:p01`，本地文件路径为 `source`。
3. 服务端指定 `tenant`，LLM 只能提供 `query` 和 `top_k`；跨租户文档在计算评分前被过滤。
4. BM25 仅是词法排序；不提供 embeddings 或语义相关度保证。

## Tool result contract

```json
{"status":"ok","hits":[{"chunk_id":"refund_approval:p01","title":"Refund Approval Rules","source":"datasets/policy_docs/refund_approval.md","text":"..."}]}
```

无匹配时：`{"status":"no_evidence","hits":[]}`。非法参数与系统异常不会伪装成 `no_evidence`。

## Model answer contract

```json
{"status":"supported","citations":[{"chunk_id":"refund_approval:p01","quote":"EXACT contiguous source text"}]}
```

或明确退让：`{"status":"insufficient_evidence","citations":[]}`。

## Verification

- 答案必须是合法、无额外字段的 JSON。
- 每条引用必须是**本次检索缓存**里存在的 chunk ID。
- 每段 quote 必须完整存在于对应原文且长度达到本项目的最小阈值。
- 最终显示只含经过确认的直接引文与来源；不显示 LLM 自由摘要。

## Non-guarantees

- 不验证跨句子推理、矛盾、语义蕴含或原始文档真实性。
- 不把经过引用校验视作 Prompt Injection 防御已经完成。
- 不实现生产身份系统、向量检索或大规模性能指标。

## Tests

`projects/p1_agent_harness/tests/test_retrieval_grounding.py` 覆盖伪造引用、错误 quote、缺失文档、租户越界、恶意路径、工具 Schema、两轮模型交接和检索质量。

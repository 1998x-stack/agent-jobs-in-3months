# A06 · 文件级 BM25 检索与检索评测：Concept Notes

## Why / What / How

将 Markdown 文件切分为稳定段落 ID，再对授权范围内的文本执行 BM25 排序。召回率、MRR 和未知问题的无证据准确率都要评测。

## 数据模型与边界

本批实现的是真实本地文档读取 + BM25 词法检索，不是 embeddings 或语义混合检索

## 正确性检查

- **Happy path**：存在一条可信结果时能够返回带来源的输出。
- **Missing evidence**：找不到文档时必须显式退让，不能猜测。
- **Invalid input**：错误参数、未授权工具或伪造来源不得通过。
- **Trace**：记录工具名称与状态，不记录密钥或不必要的原始用户数据。

## 工程源代码

`projects/p1_agent_harness/src/agent_harness/policy_search.py`

## 实验问题

- 如何从模型生成的参数中剥离租户权限？
- 为什么不能把数据库超时当成「检索不到」？
- 如果回答引用的是正确文件，但错误地推导出结论，现有校验为什么仍然不够？

## 下一步

增加 embedding + reranker、人工校准的语义忠实度评测和可复现 hard negatives。

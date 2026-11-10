# A07 · 可验证引文与无证据退让：Concept Notes

## Why / What / How

模型输出不能因为附上 [source] 就自动可信。引文要引用本轮实际检索的 chunk_id，且 quote 必须是该 chunk 的原文连续片段。

## 数据模型与边界

只校验出处与原文一致性，不证明问答推断的事实性或语义蕴含

## 正确性检查

- **Happy path**：存在一条可信结果时能够返回带来源的输出。
- **Missing evidence**：找不到文档时必须显式退让，不能猜测。
- **Invalid input**：错误参数、未授权工具或伪造来源不得通过。
- **Trace**：记录工具名称与状态，不记录密钥或不必要的原始用户数据。

## 工程源代码

`projects/p1_agent_harness/src/agent_harness/grounding.py`

## 实验问题

- 如何从模型生成的参数中剥离租户权限？
- 为什么不能把数据库超时当成「检索不到」？
- 如果回答引用的是正确文件，但错误地推导出结论，现有校验为什么仍然不够？

## 下一步

增加 embedding + reranker、人工校准的语义忠实度评测和可复现 hard negatives。

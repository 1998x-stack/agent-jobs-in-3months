# A06 · 文件级 BM25 检索与检索评测

**状态：已实现独立练习、P1 模块及无网络测试。**

## 学习目标

将 Markdown 文件切分为稳定段落 ID，再对授权范围内的文本执行 BM25 排序。召回率、MRR 和未知问题的无证据准确率都要评测。

## 具体练习

1. 阅读 [concept.md](concept.md)，理解失效路径。
2. 阅读 [exercise.py](exercise.py)，自行修改一条规则。
3. 从本目录运行 `python check_exercise.py`。
4. 对照 P1 工程源码理解工具链与跨模块数据流。
5. 在仓库根目录运行 `python -m pytest`。

## 完成标准

- [x] 最小 Python 练习可执行
- [x] 单元测试包含异常与越界输入
- [x] 已连接到 P1 的文件检索/引用验证
- [ ] 学习者独立复写、设计新反例并记录 trace

## 重要边界

本批实现的是真实本地文档读取 + BM25 词法检索，不是 embeddings 或语义混合检索

## P1 对应源码

`policy_search.py、retrieval_eval.py`

[项目文档](../../../projects/p1_agent_harness/README.md)

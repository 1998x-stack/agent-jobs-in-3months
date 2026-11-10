# A07 · 可验证引文与无证据退让

**状态：已实现独立练习、P1 模块及无网络测试。**

## 学习目标

模型输出不能因为附上 [source] 就自动可信。引文要引用本轮实际检索的 chunk_id，且 quote 必须是该 chunk 的原文连续片段。

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

只校验出处与原文一致性，不证明问答推断的事实性或语义蕴含

## P1 对应源码

`grounding.py、grounded_demo.py`

[项目文档](../../../projects/p1_agent_harness/README.md)

# A05 · 工具契约与失败语义

**状态：已实现独立练习、P1 模块及无网络测试。**

## 学习目标

模型提出工具请求不意味着授权。工具要明确只读/写入、副作用、参数、输出、权限和失败语义。业务无结果应返回 no_evidence，系统异常必须显式抛出。

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

读取工具约束、schema 校验、no_evidence 与 fail-closed 边界

## P1 对应源码

`retrieval_tools.py、typed_tools.py`

[项目文档](../../../projects/p1_agent_harness/README.md)

# A02 · Pydantic / Strict JSON Schema

## 核心概念

JSON Schema 约束模型应产生的结构；Python 服务端仍然必须独立验证输入类型、额外字段和业务约束。

## 对应 P1 工程实现

schemas.py 及 typed_tools.py 将 Pydantic 校验与严格工具 schema 连接起来。

## 实验步骤

1. 阅读本单元 exercise.py，解释每个输入字段为什么存在。
2. 从本目录运行 `python check_exercise.py`，观察 PASS。
3. 修改一个非法参数，解释为什么必须在 Python 层拒绝。
4. 对照 P1 的真实模型执行链，区分 API 接入与本地执行权限。

## 工程边界

API 成功返回不代表任务完成；工具输出和模型输出均应视为不可信数据。默认教学 Agent 不能发起真实退款。

## 官方资料

[OpenAI API 文档](https://developers.openai.com/api/docs/guides/structured-outputs)

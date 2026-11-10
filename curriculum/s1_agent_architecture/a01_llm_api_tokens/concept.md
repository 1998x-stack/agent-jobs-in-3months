# A01 · LLM API / Model Adapter / Token Budget

## 核心概念

模型调用是带 user role 的输入消息加独立 instructions；max_output_tokens 限制每次生成（可能包含推理 token），不是整个 Agent 的价格预算。

## 对应 P1 工程实现

llm.py 与 openai_adapter.py 提供对 SDK 的适配，统一返回 ModelTurn。

## 实验步骤

1. 阅读本单元 exercise.py，解释每个输入字段为什么存在。
2. 从本目录运行 `python check_exercise.py`，观察 PASS。
3. 修改一个非法参数，解释为什么必须在 Python 层拒绝。
4. 对照 P1 的真实模型执行链，区分 API 接入与本地执行权限。

## 工程边界

API 成功返回不代表任务完成；工具输出和模型输出均应视为不可信数据。默认教学 Agent 不能发起真实退款。

## 官方资料

[OpenAI API 文档](https://developers.openai.com/api/docs/guides/responses)

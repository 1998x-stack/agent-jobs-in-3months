# A04 · Observe–Decide–Act / Budget

## 核心概念

Agent Loop 在模型调用、受控工具执行和工具反馈之间迭代。终止条件必须包括成功、协议异常、模型轮次耗尽和工具次数耗尽。

## 对应 P1 工程实现

live_loop.py 用 ModelAdapter、ValidatedToolRegistry 连接完整闭环，并保留安全 Trace。

## 实验步骤

1. 阅读本单元 exercise.py，解释每个输入字段为什么存在。
2. 从本目录运行 `python check_exercise.py`，观察 PASS。
3. 修改一个非法参数，解释为什么必须在 Python 层拒绝。
4. 对照 P1 的真实模型执行链，区分 API 接入与本地执行权限。

## 工程边界

API 成功返回不代表任务完成；工具输出和模型输出均应视为不可信数据。默认教学 Agent 不能发起真实退款。

## 官方资料

[OpenAI API 文档](https://developers.openai.com/api/docs/guides/function-calling)

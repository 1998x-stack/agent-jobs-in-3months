# B10 · Observability & SLO

**状态：最小代码、P2 工程实现和负面测试已补齐。**

## 学习目标

脱敏指标、p95 和错误率

只允许记录低基数操作/结果标签和数字指标；样本不足时不宣称达标，离线成本未知时应返回 null。

## 练习路径

1. 阅读 [concept.md](concept.md) 理解失败模式。
2. 阅读 [exercise.py](exercise.py) 的输入与拒绝条件。
3. 在本目录运行 `python check_exercise.py`。
4. 阅读 [P2 observability.py](../../../projects/p2_cloud_runtime/src/agent_runtime/observability.py)。
5. 在根目录运行 `python -m pytest`。

## 验收

- [x] 可运行独立练习、失败和边界自测
- [x] 已接入 P2 实际 HTTP/Worker 模块
- [x] 安全反例纳入 GitHub CI
- [ ] 学习者独立复写并记录设计取舍
- [ ] 制作生产替代方案的威胁模型和失效实验

## 工程说明

[P2 安全架构与观测性](../../../projects/p2_cloud_runtime/README.md)。此教学代码不能用于真实支付、真实客户数据或不可信任意代码执行。

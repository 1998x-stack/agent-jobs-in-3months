# C08 · 错误分析与数据挖掘

**Track:** S3 — Agent Evals, Optimization & Learning

## 1. 核心概念

failure taxonomy / trace mining

## 2. 最小代码挑战

将失败分类为检索、规划、工具等

## 3. 接口

- 实现 `exercise.py` 中的 `solve(input_data: dict) -> dict`。
- 保留对异常、权限和边界输入的显式处理；不使用不必要的框架。
- 运行 `python check_exercise.py`；替换示例断言为该能力的具体检查。

## 4. 验收标准

可输出具体回归样本

## 5. 项目组合

完成后，思考如何将此能力引入 [p3_eval_learning_lab](../../../projects/p3_eval_learning_lab/README.md)。

## 6. 学习证据（TODO）

- [ ] 用自己的话解释概念、边界和适用场景
- [ ] 最小实现 + 单元测试
- [ ] 反例/故障注入
- [ ] 记录设计取舍与失败案例
- [ ] 在对应项目中集成

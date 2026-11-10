# Datasets

- `synthetic_cases.jsonl`：合成的、无真实用户数据的任务级评测样例。
- `policy_fixture.md`：演示性政策信息，非真实企业政策。

## JSONL contract

`id`, `expected_outcome`, `required_tools` 必需；`forbidden_tools` 可选。

生产级基准要进一步添加：任务前置状态、期望状态 diff、环境版本、策略版本、任务难度、评分依据、数据来源、保留集归属、敏感内容处理规则。

禁止将真实客户数据或 API keys 存在本目录。

# P1 · Mini Agent Harness

**Problem:** 让模型的工具动作在可信执行边界中完成多步骤任务。

## MVP（可运行参考）

- `agent_harness.models`：Action / Trace 结果模型。
- `agent_harness.tools`：明确 allowlist 的工具执行器。
- `agent_harness.planner`：离线规则型 Planner（不是 LLM）。
- `agent_harness.loop`：Agent Loop、预算与停止逻辑。
- `agent_harness.context`：最近观察结果截断；非生产 Context Engineering。
- `agent_harness.memory`：仅内存多租户隔离存储。
- `agent_harness.security`：最小租户等值检查。

## 运行

```bash
PYTHONPATH=projects/p1_agent_harness/src python -m agent_harness.demo
python -m pytest projects/p1_agent_harness/tests
```

## 进阶功能占位

- [ ] 真实 LLM Adapter、结构化 ToolCall 参数验证
- [ ] 混合 RAG、来源校验与动态上下文压缩
- [ ] MCP client / server、Multi-agent handoff
- [ ] 持久 Memory、失败恢复、模型输出安全校验

## 退出标准

至少 20 个合成任务、工具授权单测、终止预算测试、完整轨迹、可重放失败案例；写明模型行为非确定性的控制方法。

---

## A01–A04 · Live Responses API Agent (new)

这里新增可使用真实 OpenAI 模型的版本，但默认仍保持完全离线的测试路径。

### 运行真实模型

```bash
python -m pip install -e '.[dev,llm]'
export OPENAI_API_KEY='your-own-api-key'
export OPENAI_MODEL='gpt-5-mini'
PYTHONPATH=projects/p1_agent_harness/src python -m agent_harness.live_demo --goal "Look up the 'refund' policy"
```

**该命令会产生实际的 API 费用；CI 没有使用真实密钥或付费模型。**

### 源码对应

| Unit | Files | Focus |
|---|---|---|
| A01 | llm.py, openai_adapter.py | ModelAdapter / Responses API / token cap |
| A02 | schemas.py, typed_tools.py | Strict JSON Schema + Pydantic validation |
| A03 | typed_tools.py | Read-only allowlist / call_id / tool feedback |
| A04 | live_loop.py | Observe-Decide-Act, budgets, sanitized trace |

### 实际执行路径

```mermaid
sequenceDiagram
 participant U as User
 participant L as Agent Loop
 participant M as Responses API
 participant T as Safe Tool Registry
 U->>L: Goal
 L->>M: User input and strict tool schemas
 M-->>L: function_call with call_id
 L->>T: Allowlist and Pydantic validation
 T-->>L: JSON tool result
 L->>M: function_call_output and previous_response_id
 M-->>L: Final answer
 L-->>U: Answer and sanitized trace
```

### 测试

```bash
python -m pytest projects/p1_agent_harness/tests tests/test_atomic_a01_a04.py
```

**隐私与合规：** 教学适配器显式设置 `store=True` 支持 `previous_response_id` 多轮链。不要发送真实客户数据、密钥和敏感轨迹。生产环境必须检查数据保留政策，并考虑无状态方案。

**局限：** 只允许只读政策查询；真实检索、多 Agent、OAuth、人工审批、分布式恢复尚未实现。参考 API 规范：[Function Calling](https://developers.openai.com/api/docs/guides/function-calling)。

---

## A05–A07 · Document Retrieval + Verifiable Citations (new)

本批将固定字典策略查询升级为**读取本仓库 Markdown 文件**的 BM25 词法检索，并添加严格的摘录式引用校验；现有 A01–A04 live demo 保留兼容。

### 快速运行：完全离线、无需 API Key

```bash
PYTHONPATH=projects/p1_agent_harness/src python -m agent_harness.grounded_demo --question "refund proposal human approval"
PYTHONPATH=projects/p1_agent_harness/src python -m agent_harness.retrieval_eval
python -m pytest projects/p1_agent_harness/tests tests/test_atomic_a05_a07.py
```

### 可选：真实 LLM + 搜索工具 + 验证引用

```bash
python -m pip install -e '.[dev,llm]'
export OPENAI_API_KEY='your-own-api-key'
PYTHONPATH=projects/p1_agent_harness/src python -m agent_harness.grounded_demo --live --question "Does a refund proposal transfer money before approval?"
```

真实模式会消耗 API 费用；CI 使用 Fake ModelAdapter，不进行在线推理。多轮 Responses 示例使用 `store=True`，请勿传输敏感或真实客户数据。

### 本批新增模块

| Module | Purpose |
|---|---|
| `policy_search.py` | Markdown manifest、段落 chunking、稳定 ID、scope 过滤及 BM25 |
| `retrieval_tools.py` | 只读 `search_policy(query, top_k)` 工具；查询与租户权限分离 |
| `grounding.py` | JSON 答案契约、引用 ID + exact quote 校验、无证据退让 |
| `grounded_demo.py` | 离线摘录式演示，以及可选真实 LLM 搜索 |
| `retrieval_eval.py` | 合成标签数据的 Macro Recall@k、MRR@k、No-evidence Accuracy |

### Grounding 的确切保证

只有模型引用了**本轮实际返回**的 chunk，且引用的 `quote` 是该 chunk 中原样连续片段，才能展示。没有来源、引用造假、自由叙述或额外 JSON 字段均被拒绝。展示结果只由这些已验证原文摘录组成。

**注意：这是来源与摘录验证，不是语义蕴含判断。** 引用正确不保证引用的材料回答了问题；当前语料均为虚构政策，不能用于真实退款决策。对 Prompt Injection 的防护依然需要进一步实验。

### 数据来源和扩展路线

所有检索文档均位于 [datasets/policy_docs](../../datasets/policy_docs/)，含租户隔离测试用的虚构内部文档。现阶段不使用 embedding / vector database / reranker，因此不要把结果宣传为语义混合 RAG。后续可引入向量召回、RRF 与语义 Grader。

### 技术数据流

```mermaid
flowchart TD
 Q[User Question] --> M[Model / Fake Model]
 M --> T[Typed Search Tool]
 T --> A[Tenant-scoped BM25]
 A --> D[Markdown Chunks and Source IDs]
 D --> E[Per-run Evidence Cache]
 E --> V[Extractive Citation Verifier]
 M --> V
 V -->|Valid exact quote| O[Grounded Source Excerpts]
 V -->|Invalid / no evidence| X[Reject or Abstain]
```

# Agent Jobs in 3 Months · AI Agent Engineer Roadmap

> **30 个元能力 × 3 个递进工程项目 × 12 周学习路线**
>
> A code-first learning repository for AI Agent Architecture, Production Agent Systems, and Agent Evaluation & Learning.

## 🎯 目标

通过可验证的代码与工程证据，系统掌握：

| Track | 核心问题 | 产物 |
|---|---|---|
| **S1 · Agent Architecture** | Agent 怎样准确地完成多步骤任务？ | P1 Mini Agent Harness |
| **S2 · Production Systems** | Agent 怎样可靠、安全、规模化运行？ | P2 Agent Cloud Runtime |
| **S3 · Evaluation & Learning** | 怎样定位失败并证明 Agent 变好了？ | P3 Agent Evaluation & Learning Lab |

> **范围说明**：12 周是针对具备 Python / Git 基础的学习与作品集冲刺期，不代表 12 周能够获得 Staff/Principal 级岗位所要求的多年生产经验。

## 🗂️ Code Categories

- `curriculum/`：30 个元能力，每个单元包括概念、最小练习、验证测试、完成条件。
- `projects/`：P1/P2/P3 递进工程项目；从基础 MVP 到生产级扩展的 TODO 清晰分离。
- `docs/roadmaps/`：技能、概念、代码、项目四条 Mermaid 路线。
- `docs/architecture/`：系统边界、ADR、Threat Model、Telemetry、Eval 数据规范。
- `docs/guides/`：学习方法、项目验收、面试故事、作品集、Glossary。
- `weeks/`：W01–W12 每周目标、实验与验收。
- `datasets/`：合成任务、评测数据契约和样例。
- `scripts/`：环境、路径与里程碑辅助脚本。
- `tests/`：仓库级 Smoke / Contract 测试。
- `.github/`：贡献模板与 CI。

## 🚀 快速开始

```bash
git clone https://github.com/1998x-stack/agent-jobs-in-3months.git
cd agent-jobs-in-3months
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
python -m pip install -e '.[dev]'
python -m pytest
python scripts/check_progress.py
```

30 个单元中的练习文件是**刻意留下的 TODO**，其测试使用严格 expected-failure 标记；这不是生产功能已完成的宣称。三个工程项目提供最小可运行参考实现与明确的后续扩展接口。

## 🧭 学习顺序

1. **W01–W04**：S1 单元 → P1 Agent Loop → Tool Registry → Context / Memory / Trace。
2. **W05–W08**：S2 单元 → P2 Durable Workflow → Idempotency → Approval → Security。
3. **W09–W12**：S3 单元 → P3 Task Oracle → Trajectory / Cost / Safety Evals → Controlled Experiments。

完整计划见 [12 周路线](ROADMAP.md)、[能力矩阵](SKILL_MATRIX.md)、[课程目录](curriculum/README.md)、[工程目录](projects/README.md)。

## ✅ Definition of Done

每个元能力完成时应满足：**能解释原理、能写出最小实现、能通过自己设计的测试、能说明局限与失败模式**。每个项目要有可复现 Demo、自动化测试、关键设计决策（ADR）、性能与可靠性证据，以及用户能独立运行的命令。

**Never commit API keys, credentials, real customer data, or private model traces.** 所有默认数据均应使用合成样例。

## 📜 研究与资料

市场研究是用于选择高价值技能方向，不是薪资承诺；详见 [Job Market Notes](docs/research/job-market.md) 与 [参考资料](docs/guides/references.md)。

## 🧩 状态

**Scaffold / 学习骨架已建立。** `curriculum` 下的教学练习尚需逐项实现，`projects` 中的进阶能力也是显式 TODO。请勿将其视为可以直接用于生产、支付或处理敏感客户数据的软件。

---

## A01–A04：真实模型执行链（已添加）

在 [P1 Live Agent](projects/p1_agent_harness/README.md) 中，新增了可选 OpenAI Responses API 执行版本：
ModelAdapter → Strict JSON Schema / Pydantic → Read-only Tool Registry → Agent Loop。

```bash
python -m pip install -e '.[dev,llm]'
export OPENAI_API_KEY='your-own-api-key'
PYTHONPATH=projects/p1_agent_harness/src python -m agent_harness.live_demo --goal "Look up refund policy"
```

该运行会消耗实际 API 费用。CI 通过 Fake Responses 客户端验证行为，不调用模型。
**注意：** Live Demo 使用 `store=True` 关联多轮请求，不要提交真实隐私数据或生产密钥。
新增的 A01–A04 基础练习可以直接执行 `python check_exercise.py`；其他课程单元仍保留 TODO。

---

## A05–A07：文档检索与可验证引用（新增）

从 `datasets/policy_docs/*.md` 读取虚构 Markdown 文档，做 BM25 检索、稳定 chunk 引用、租户过滤和离线评测。

```bash
PYTHONPATH=projects/p1_agent_harness/src python -m agent_harness.grounded_demo --question "refund approval"
PYTHONPATH=projects/p1_agent_harness/src python -m agent_harness.retrieval_eval
```

带真实模型的模式在 [P1 文档](projects/p1_agent_harness/README.md) 中。**实时模型调用是付费且需显式 `--live`；CI 全程使用假模型适配器。**

目前 A01–A07 的基础练习已实现；A08–C10 仍保留待完成。检索采用词法 BM25 而非 embeddings；引用保证原文出处可验证，不保证完整语义事实正确。

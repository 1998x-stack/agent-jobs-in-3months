# 12-Week Build Roadmap

## 三阶段里程碑

| 阶段 | 周数 | 核心项目 | 交付证据 |
|---|---|---|---|
| Foundation | W01–W04 | P1 Agent Harness | Loop、Tools、Context、Trace、权限测试 |
| Reliability | W05–W08 | P2 Cloud Runtime | 持久状态、幂等、Lease、审批、故障演练 |
| Evidence | W09–W12 | P3 Eval Lab | 数据集、Oracle、配对评测、消融实验、报告 |

## 每周路线

- [W01](weeks/w01/README.md) — A01–A03：模型接口、Schema、工具调用；交付：P1 工具协议和注册表
- [W02](weeks/w02/README.md) — A04–A07：Agent Loop、工具契约、检索、证据；交付：P1 最小多步任务
- [W03](weeks/w03/README.md) — A08–A10：Context、Memory、Planning / MCP；交付：P1 状态和代理交接
- [W04](weeks/w04/README.md) — P1 集成、回放与失败演练；交付：P1 设计文档、测试和 Demo
- [W05](weeks/w05/README.md) — B01–B03：API、SQL、幂等；交付：P2 任务提交和唯一约束
- [W06](weeks/w06/README.md) — B04–B06：Queue、Lease、Checkpoint；交付：P2 竞争领取和故障恢复
- [W07](weeks/w07/README.md) — B07–B09：审批、授权、沙箱；交付：P2 最小权限和模拟隔离
- [W08](weeks/w08/README.md) — B10：Trace、SLO，P2 压测；交付：P2 SLO 记录与故障复盘
- [W09](weeks/w09/README.md) — C01–C03：数据集、真值、轨迹评测；交付：P3 Grader 和任务 Schema
- [W10](weeks/w10/README.md) — C04–C05：安全评测和统计；交付：P3 对抗集和 Bootstrap
- [W11](weeks/w11/README.md) — C06–C08：消融、成本、失败挖掘；交付：P3 配对实验报告
- [W12](weeks/w12/README.md) — C09–C10：SFT / DPO / RL 基础；作品集包装；交付：最终设计、Demo、证据索引

## 定义完成

每周需要提供：可运行命令、至少一个回归测试、至少一个失败示例、具体 commit/PR 链接、下一周的明确风险。

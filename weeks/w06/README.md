# W06 · Queue, Leases, Retries and Durable Execution

## 本周元能力

- [B04 · Workers & Backpressure](../../curriculum/s2_production_systems/b04_queue_workers/README.md)
- [B05 · Leases & Bounded Retries](../../curriculum/s2_production_systems/b05_leases_retries/README.md)
- [B06 · Durable Checkpoint / Resume](../../curriculum/s2_production_systems/b06_durable_execution/README.md)

## 工程交付

- [x] SQLite 持久化队列 + 有上限的多线程 Worker 批处理
- [x] Worker 竞争领取、按数据库事务 fencing，不重复领取一个 active task
- [x] 租约心跳、过期接管、陈旧 Worker 写入拒绝
- [x] 仅临时故障自动重试，指数退避 + jitter + 延迟任务可见时间
- [x] Plan 与每个已验证 Researcher 子任务逐步 Checkpoint
- [x] 重新打开 SQLite 后跳过已提交步骤并重做未完成步骤
- [x] B04–B06 最小练习和仓库 CI 集成
- [ ] 长任务自动定时心跳、真正消息 Broker 与跨主机部署
- [ ] 副作用 Outbox、补偿/对账与严格数据治理

## 运行

```bash
python -m pip install -e '.[dev,api]'
PYTHONPATH=projects/p1_agent_harness/src:projects/p2_cloud_runtime/src python -m agent_runtime.durability_demo
python -m pytest
python scripts/check_progress.py
```

## 验收证据

`projects/p2_cloud_runtime/tests/test_durable_workers.py` 覆盖并发 Worker、过期租约、延迟可领取性、心跳、Checkpoint 的不可变性、故障恢复、旧数据库迁移。

## 局限

仅对**成功写入 Checkpoint 的步骤**有跳过式重放；没有实现任意外部动作的 exactly-once，Worker 长时间阻塞时也需更多心跳治理。

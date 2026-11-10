# B06 · Checkpoint / Crash Recovery 核心概念

## 核心原理

稳定步骤、不可变落盘检查点与中断后重放

## 不变量

- `BEGIN IMMEDIATE` 为事务性领取/修改提供互斥写锁。
- 只有持有当前、未过期 fencing token 的 Worker 才允许提交数据库状态。
- 超出允许尝试次数必须进入终止状态。
- 已提交的 Checkpoint 不应被不同结果覆盖，恢复时仅重做未保存的子任务。

## 故障注入

1. 两个 Worker 同时领取单个排队任务。
2. Lease 过期后旧 Worker 尝试心跳和完成。
3. 第一个 Researcher 子任务提交 Checkpoint 后强制中断。
4. 重新打开 SQLite 文件后恢复并验证旧步骤不会重跑。

## 不能保证的能力

SQLite 不是外部消息 Broker；没有生产级长期心跳、自恢复进程监督、外部副作用幂等或真正分布式调度。

## 源码

[P2 Runtime](../../../projects/p2_cloud_runtime/README.md) · [集成测试](../../../projects/p2_cloud_runtime/tests/test_durable_workers.py)

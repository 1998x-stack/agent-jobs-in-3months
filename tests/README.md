# Test strategy

- Repo smoke tests：目录结构和全部 30 个元能力完整性。
- P1/P2/P3：Reference MVP 的基础行为测试。
- 课程练习的 `check_exercise.py`：刻意初始失败，需要学习者实现 TODO 后逐一验证。

```bash
python -m pytest
python scripts/check_progress.py
```

TODO：property-based tests、故障注入、端到端 trajectory regression、security tests、performance baselines。

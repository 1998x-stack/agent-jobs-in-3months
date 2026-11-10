import pytest
from agent_harness.context import recent_observations
from agent_harness.loop import run_agent
from agent_harness.memory import MemoryStore
from agent_harness.models import Action
from agent_harness.planner import LookupThenFinish
from agent_harness.security import require_tenant
from agent_harness.tools import ToolRegistry

def test_agent_loop_and_trace():
    tools = ToolRegistry()
    tools.register("lookup_policy", lambda topic: f"policy:{topic}")
    result = run_agent("refund", LookupThenFinish(), tools)
    assert result.output == "policy:refund"
    assert len(result.trace) == 1

def test_unknown_tool_is_rejected():
    with pytest.raises(PermissionError):
        ToolRegistry().execute("dangerous_delete", {})

def test_step_budget():
    class Endless:
        def decide(self, state):
            return Action(kind="tool", name="noop")
    tools = ToolRegistry()
    tools.register("noop", lambda: "ok")
    with pytest.raises(RuntimeError, match="budget"):
        run_agent("x", Endless(), tools, max_steps=2)

def test_memory_and_tenant_isolation():
    store = MemoryStore()
    store.put("tenant_a", "key", "private")
    assert store.get("tenant_b", "key") is None
    with pytest.raises(PermissionError):
        require_tenant("tenant_a", "tenant_b")

def test_context_budget_is_explicit():
    assert recent_observations([1, 2, 3], max_items=2) == [2, 3]

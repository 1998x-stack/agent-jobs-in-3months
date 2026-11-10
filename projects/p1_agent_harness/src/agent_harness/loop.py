"""Agent loop with explicit step budget, trace, and tool boundary."""
from .models import AgentResult, TraceStep
from .tools import ToolRegistry

def run_agent(goal: str, planner: object, tools: ToolRegistry,
              max_steps: int = 6) -> AgentResult:
    if max_steps < 1:
        raise ValueError("max_steps must be positive")
    state: dict = {"goal": goal, "observations": []}
    trace: list[TraceStep] = []
    for step in range(max_steps):
        action = planner.decide(state)
        if action.kind == "finish":
            return AgentResult(action.output, trace)
        if action.kind != "tool":
            raise ValueError("unknown action kind")
        result = tools.execute(action.name, action.arguments)
        state["observations"].append({"tool": action.name, "result": result})
        trace.append(TraceStep(step + 1, action.name, result))
    raise RuntimeError("agent step budget exhausted")

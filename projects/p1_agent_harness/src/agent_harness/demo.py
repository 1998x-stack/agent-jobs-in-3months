"""Run: PYTHONPATH=projects/p1_agent_harness/src python -m agent_harness.demo"""
from .loop import run_agent
from .planner import LookupThenFinish
from .retrieval import lookup_policy
from .tools import ToolRegistry
from .trace import summarize

def main() -> None:
    tools = ToolRegistry()
    tools.register("lookup_policy", lookup_policy)
    result = run_agent("refund", LookupThenFinish(), tools)
    print("Final:", result.output)
    print("Trace:", summarize(result))

if __name__ == "__main__":
    main()

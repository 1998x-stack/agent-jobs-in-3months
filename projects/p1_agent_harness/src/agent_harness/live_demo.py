"""Run with a real model only after setting OPENAI_API_KEY.

pip install -e '.[dev,llm]'
OPENAI_API_KEY=... python -m agent_harness.live_demo --goal "Look up refund policy"
"""
import argparse
import os

from .live_loop import run_live_agent
from .openai_adapter import OpenAIResponsesAdapter
from .retrieval import lookup_policy
from .schemas import PolicyLookupArgs
from .typed_tools import ValidatedToolRegistry


def build_read_only_tools() -> ValidatedToolRegistry:
    tools = ValidatedToolRegistry()
    tools.register(
        name="lookup_policy",
        description=(
            "Retrieve an example teaching policy by its exact topic. "
            "The only available topic is 'refund'. Read-only."
        ),
        arguments=PolicyLookupArgs,
        callback=lookup_policy,
    )
    return tools


def main() -> None:
    parser = argparse.ArgumentParser(description="P1 live, read-only AI agent")
    parser.add_argument(
        "--goal",
        default="Look up the 'refund' policy and explain whether a refund can be executed automatically.",
    )
    parser.add_argument("--model", default=os.getenv("OPENAI_MODEL", "gpt-5-mini"))
    parser.add_argument("--max-turns", type=int, default=6)
    args = parser.parse_args()
    if not os.getenv("OPENAI_API_KEY"):
        parser.error("OPENAI_API_KEY is missing; do not put keys in source code")
    adapter = OpenAIResponsesAdapter(model=args.model)
    result = run_live_agent(
        args.goal, adapter, build_read_only_tools(), max_model_turns=args.max_turns
    )
    print("Answer:", result.output)
    print("Tool calls:", [step.action for step in result.trace])


if __name__ == "__main__":
    main()

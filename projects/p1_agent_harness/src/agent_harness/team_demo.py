"""A08-A10 integrated P1 team demo. Offline by default, no API key.

Run:
  PYTHONPATH=projects/p1_agent_harness/src python -m agent_harness.team_demo

To explicitly call the paid Responses API:
  PYTHONPATH=projects/p1_agent_harness/src python -m agent_harness.team_demo --live
"""
import argparse
import os

from .agent_team import TeamCoordinator
from .grounding import GROUNDING_INSTRUCTIONS
from .policy_search import demo_corpus
from .scoped_memory import MemoryScope, ScopedMemoryStore


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Planner -> Researcher -> Reviewer with scoped memory"
    )
    parser.add_argument(
        "--question",
        default=(
            "refund proposal transfer money human approval "
            "and approved refund processing five business days"
        ),
    )
    parser.add_argument("--tenant", default="demo-tenant")
    parser.add_argument("--user", default="demo-user")
    parser.add_argument("--db", default=":memory:", help="local SQLite path")
    parser.add_argument(
        "--remember",
        default=None,
        help="explicit opt-in non-sensitive user fact, e.g. preference=brief",
    )
    parser.add_argument("--live", action="store_true", help="paid OpenAI API calls")
    parser.add_argument("--model", default=os.getenv("OPENAI_MODEL", "gpt-5-mini"))
    args = parser.parse_args()

    adapter_factory = None
    if args.live:
        if not os.getenv("OPENAI_API_KEY"):
            parser.error("--live requires OPENAI_API_KEY")
        from .openai_adapter import OpenAIResponsesAdapter
        adapter_factory = lambda query: OpenAIResponsesAdapter(
            model=args.model, instructions=GROUNDING_INSTRUCTIONS
        )

    scope = MemoryScope(args.tenant, args.user)
    with ScopedMemoryStore(args.db) as memory:
        if args.remember:
            if "=" not in args.remember:
                parser.error("--remember requires key=value")
            key, value = args.remember.split("=", 1)
            memory.put(
                scope, key, value, source="explicit_user", ttl_seconds=3600
            )
        run = TeamCoordinator(
            demo_corpus(), memory, adapter_factory=adapter_factory
        ).run(args.question, scope=scope)

    print("Mode:", "live Responses API (paid)" if args.live else "offline deterministic")
    print("Status:", run.status)
    print("Answer:\n", run.text)
    print("Citations:", list(run.citation_ids))
    print("Handoffs:", [
        f"{event.source_role}->{event.target_role}:{event.status}"
        for event in run.handoffs
    ])
    print("Context sources:", [
        list(report.selected_ids) for report in run.context_reports
    ])


if __name__ == "__main__":
    main()

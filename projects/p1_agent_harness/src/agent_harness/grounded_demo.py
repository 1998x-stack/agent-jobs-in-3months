"""A05-A07 demo: default offline, optional actual LLM via --live.

Offline:
  PYTHONPATH=projects/p1_agent_harness/src python -m agent_harness.grounded_demo
Live (paid, API key required, Responses store=True):
  PYTHONPATH=projects/p1_agent_harness/src python -m agent_harness.grounded_demo --live
"""
import argparse
import json
import os

from .grounding import (
    GROUNDING_INSTRUCTIONS,
    run_grounded_agent,
    verify_extractive_answer,
)
from .openai_adapter import OpenAIResponsesAdapter
from .policy_search import demo_corpus
from .retrieval_tools import RetrievalSession


def main() -> None:
    parser = argparse.ArgumentParser(description="Citation-verified policy retrieval")
    parser.add_argument(
        "--question",
        default="Does a refund proposal transfer money without human approval?",
    )
    parser.add_argument("--tenant", default="public-demo")
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--model", default=os.getenv("OPENAI_MODEL", "gpt-5-mini"))
    parser.add_argument("--live", action="store_true", help="call the paid OpenAI API")
    args = parser.parse_args()

    corpus = demo_corpus()
    if args.live:
        if not os.getenv("OPENAI_API_KEY"):
            parser.error("--live requires OPENAI_API_KEY")
        adapter = OpenAIResponsesAdapter(
            model=args.model, instructions=GROUNDING_INSTRUCTIONS
        )
        run = run_grounded_agent(
            args.question, adapter, corpus, tenant=args.tenant
        )
        print(run.answer.text)
        print("Tools used:", [step.action for step in run.trace])
        return

    # Deterministic offline retrieval. Uses the same final quote verifier as
    # the live LLM path, without pretending to generate a natural-language answer.
    session = RetrievalSession(corpus, tenant=args.tenant)
    result = session.search_policy(query=args.question, top_k=args.top_k)
    if result["hits"]:
        first = result["hits"][0]
        raw = {
            "status": "supported",
            "citations": [{"chunk_id": first["chunk_id"], "quote": first["text"]}],
        }
    else:
        raw = {"status": "insufficient_evidence", "citations": []}
    answer = verify_extractive_answer(json.dumps(raw), session.evidence)
    print("Mode: offline deterministic retrieval and citation validation")
    print(answer.text)


if __name__ == "__main__":
    main()

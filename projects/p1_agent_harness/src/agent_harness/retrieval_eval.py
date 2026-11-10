"""A06: offline retrieval metrics from a labeled, small synthetic holdout."""
import json
from pathlib import Path

from .policy_search import PolicyCorpus, demo_corpus


def evaluate(
    corpus: PolicyCorpus,
    cases: list[dict],
    *,
    top_k: int = 3,
) -> dict:
    """Macro recall@k, MRR@k on positive cases, no-evidence accuracy on negatives."""
    if not cases:
        raise ValueError("at least one retrieval case is required")
    recall_sum = 0.0
    reciprocal_sum = 0.0
    positive = 0
    negative = 0
    negative_correct = 0
    for case in cases:
        gold = set(case["gold_chunk_ids"])
        hits = corpus.search(case["query"], tenant=case["tenant"], top_k=top_k)
        retrieved = [hit.chunk.chunk_id for hit in hits]
        if gold:
            positive += 1
            recall_sum += len(gold.intersection(retrieved)) / len(gold)
            reciprocal_sum += next(
                (1.0 / (index + 1) for index, cid in enumerate(retrieved) if cid in gold),
                0.0,
            )
        else:
            negative += 1
            negative_correct += int(not retrieved)
    return {
        "n": len(cases),
        "positive_cases": positive,
        "negative_cases": negative,
        "recall_at_k": round(recall_sum / positive, 4) if positive else None,
        "mrr_at_k": round(reciprocal_sum / positive, 4) if positive else None,
        "no_evidence_accuracy": (
            round(negative_correct / negative, 4) if negative else None
        ),
        "top_k": top_k,
    }


def load_cases(path: str | Path) -> list[dict]:
    cases = [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]
    if len({case["id"] for case in cases}) != len(cases):
        raise ValueError("duplicate retrieval case id")
    return cases


def main() -> None:
    repo = Path(__file__).resolve().parents[4]
    cases = load_cases(repo / "datasets" / "retrieval_cases.jsonl")
    print(json.dumps(evaluate(demo_corpus(), cases), indent=2))


if __name__ == "__main__":
    main()

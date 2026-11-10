"""A06: self-contained, minimal BM25 from documents to scored citations."""
from collections import Counter
import math
import re
from typing import Any


def _terms(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.casefold())


def solve(input_data: dict[str, Any]) -> dict[str, Any]:
    docs = input_data.get("documents")
    query = input_data.get("query")
    top_k = input_data.get("top_k", 3)
    if not isinstance(docs, list) or not all(
        isinstance(doc, dict)
        and isinstance(doc.get("id"), str)
        and isinstance(doc.get("text"), str)
        for doc in docs
    ):
        raise ValueError("documents must be [{id, text}]")
    if not isinstance(query, str) or not query.strip():
        raise ValueError("query required")
    if type(top_k) is not int or top_k <= 0:
        raise ValueError("positive top_k required")
    tokens = [Counter(_terms(doc["text"])) for doc in docs]
    lengths = [sum(counts.values()) for counts in tokens]
    average = max(sum(lengths) / len(lengths), 1) if tokens else 1
    results = []
    for doc, counts, length in zip(docs, tokens, lengths):
        score = 0.0
        for term in set(_terms(query)):
            frequency = counts[term]
            if frequency == 0:
                continue
            df = sum(other[term] > 0 for other in tokens)
            idf = math.log1p((len(tokens) - df + 0.5) / (df + 0.5))
            score += idf * 2.5 * frequency / (
                frequency + 1.5 * (0.25 + 0.75 * length / average)
            )
        if score > 0:
            results.append({"doc_id": doc["id"], "score": round(score, 6)})
    results.sort(key=lambda hit: (-hit["score"], hit["doc_id"]))
    hits = results[:top_k]
    return {"status": "ok" if hits else "no_evidence", "hits": hits}

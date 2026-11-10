"""A07: reject unsupported citations using exact source excerpts."""
from typing import Any


def solve(input_data: dict[str, Any]) -> dict[str, Any]:
    evidence = input_data.get("evidence")
    citation = input_data.get("citation")
    if not isinstance(evidence, dict) or not isinstance(citation, dict):
        raise ValueError("evidence map and citation are required")
    if set(citation) != {"chunk_id", "quote"}:
        raise ValueError("citation must include only chunk_id and quote")
    chunk_id, quote = citation["chunk_id"], citation["quote"]
    if not isinstance(chunk_id, str) or chunk_id not in evidence:
        raise ValueError("source was not retrieved")
    source_text = evidence[chunk_id]
    if not isinstance(source_text, str) or not isinstance(quote, str):
        raise ValueError("source text and quote must be strings")
    if len(quote) < 12 or quote.strip() != quote or quote not in source_text:
        raise ValueError("quote must be an exact source excerpt")
    return {"status": "supported", "answer": f'"{quote}" [{chunk_id}]'}

"""A06: deterministic file-backed BM25 search with stable source/chunk identifiers.

This is *lexical* retrieval, not embeddings or semantic verification.
All documents are local synthetic fixtures. Scope is bound by the server, not
accepted as an LLM-supplied tool argument.
"""
from collections import Counter
from dataclasses import dataclass
import json
import math
from pathlib import Path
import re

_WORDS = re.compile(r"[a-z0-9]+|[\u4e00-\u9fff]+")
_IGNORED = {
    "a", "an", "and", "are", "can", "does", "for", "from", "how", "is",
    "of", "on", "or", "our", "the", "to", "what", "when", "which",
    "who", "with", "policy",
}
_ID = re.compile(r"^[a-z][a-z0-9_]*$")


def tokenize(text: str) -> tuple[str, ...]:
    """Lowercase English words; Chinese character bigrams for a basic lexical demo."""
    result = []
    for part in _WORDS.findall(text.casefold()):
        if "\u4e00" <= part[0] <= "\u9fff":
            result.extend(part[i:i + 2] for i in range(len(part) - 1)) if len(part) > 1 else result.append(part)
        elif part not in _IGNORED:
            result.append(part)
    return tuple(result)


@dataclass(frozen=True)
class PolicyChunk:
    chunk_id: str
    document_id: str
    title: str
    source: str
    scope: str
    text: str


@dataclass(frozen=True)
class SearchHit:
    chunk: PolicyChunk
    score: float

    def as_tool_dict(self) -> dict:
        return {
            "chunk_id": self.chunk.chunk_id,
            "title": self.chunk.title,
            "source": self.chunk.source,
            "text": self.chunk.text,
        }


class PolicyCorpus:
    """Read-only document index. Public documents are visible to any tenant."""

    def __init__(self, chunks: tuple[PolicyChunk, ...]) -> None:
        ids = [c.chunk_id for c in chunks]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate stable chunk IDs")
        self.chunks = chunks

    @classmethod
    def from_directory(cls, directory: str | Path) -> "PolicyCorpus":
        directory = Path(directory).resolve()
        manifest = json.loads((directory / "index.json").read_text(encoding="utf-8"))
        if not isinstance(manifest, list):
            raise ValueError("manifest must be a list")
        chunks: list[PolicyChunk] = []
        seen_ids: set[str] = set()
        for metadata in manifest:
            doc_id = metadata["id"]
            filename = metadata["file"]
            scope = metadata["scope"]
            title = metadata["title"]
            if not isinstance(doc_id, str) or not _ID.fullmatch(doc_id):
                raise ValueError("invalid document id")
            if doc_id in seen_ids:
                raise ValueError("duplicate document id")
            seen_ids.add(doc_id)
            if (
                not isinstance(filename, str)
                or Path(filename).name != filename
                or not filename.endswith(".md")
                or not (directory / filename).resolve().is_relative_to(directory)
            ):
                raise ValueError("document file must be a local Markdown file")
            if not isinstance(scope, str) or not scope:
                raise ValueError("scope required")
            if not isinstance(title, str) or not title:
                raise ValueError("title required")
            content = (directory / filename).read_text(encoding="utf-8")
            paragraphs = [
                block.strip()
                for block in re.split(r"\n\s*\n", content)
                if block.strip() and not block.lstrip().startswith("#")
            ]
            if not paragraphs:
                raise ValueError(f"no text chunks for {doc_id}")
            for index, paragraph in enumerate(paragraphs, 1):
                chunks.append(PolicyChunk(
                    chunk_id=f"{doc_id}:p{index:02d}",
                    document_id=doc_id,
                    title=title,
                    source=f"datasets/policy_docs/{filename}",
                    scope=scope,
                    text=paragraph,
                ))
        return cls(tuple(chunks))

    def search(self, query: str, *, tenant: str, top_k: int = 3) -> list[SearchHit]:
        if not isinstance(query, str) or not query.strip():
            raise ValueError("query is required")
        if not isinstance(tenant, str) or not tenant:
            raise ValueError("authenticated tenant is required")
        if type(top_k) is not int or not 1 <= top_k <= 5:
            raise ValueError("top_k must be 1..5")
        query_terms = set(tokenize(query))
        if not query_terms:
            return []
        # Filter before calculating IDF so other tenants do not affect ranking.
        visible = [chunk for chunk in self.chunks if chunk.scope in ("public", tenant)]
        if not visible:
            return []
        token_counts = [Counter(tokenize(chunk.text + " " + chunk.title)) for chunk in visible]
        lengths = [sum(counts.values()) for counts in token_counts]
        avg_len = max(sum(lengths) / len(lengths), 1.0)
        scores: list[SearchHit] = []
        for chunk, counts, length in zip(visible, token_counts, lengths):
            score = 0.0
            for word in query_terms:
                tf = counts[word]
                if tf == 0:
                    continue
                df = sum(1 for other in token_counts if other[word] > 0)
                idf = math.log1p((len(visible) - df + 0.5) / (df + 0.5))
                score += idf * (tf * 2.5) / (tf + 1.5 * (0.25 + 0.75 * length / avg_len))
            if score > 0:
                scores.append(SearchHit(chunk, score))
        scores.sort(key=lambda h: (-h.score, h.chunk.chunk_id))
        return scores[:top_k]


def demo_corpus() -> PolicyCorpus:
    """Load tracked Markdown fixtures, independent of process working directory."""
    repo = Path(__file__).resolve().parents[4]
    return PolicyCorpus.from_directory(repo / "datasets" / "policy_docs")

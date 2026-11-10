"""A08: bounded, deterministic context packing with provenance.

Uses an exact serialized-character limit, not an exact tokenizer limit.
Facts from memory, retrieval and tools are untrusted data, never instructions.
Whole blocks are discarded when they do not fit; no invented summary.
"""
from dataclasses import dataclass
import json
import math
from typing import Literal


BlockKind = Literal["memory", "evidence", "observation"]


@dataclass(frozen=True)
class ContextBlock:
    kind: BlockKind
    source_id: str
    content: str
    priority: int = 0

    def __post_init__(self) -> None:
        if self.kind not in ("memory", "evidence", "observation"):
            raise ValueError("unsupported context kind")
        if not isinstance(self.source_id, str) or not self.source_id.strip():
            raise ValueError("context source_id required")
        if not isinstance(self.content, str) or not self.content.strip():
            raise ValueError("context block content required")
        if type(self.priority) is not int or not 0 <= self.priority <= 10:
            raise ValueError("priority must be an integer in 0..10")


@dataclass(frozen=True)
class PackedContext:
    payload: str
    selected_ids: tuple[str, ...]
    dropped_ids: tuple[str, ...]
    estimated_tokens: int
    max_chars: int

    def decode(self) -> dict:
        return json.loads(self.payload)


def pack_context(
    *,
    instructions: str,
    goal: str,
    blocks: list[ContextBlock] | tuple[ContextBlock, ...] = (),
    max_chars: int = 2200,
    reserve_chars: int = 200,
) -> PackedContext:
    """Pack complete blocks under a serialized JSON length limit.

    reserve_chars is local headroom, not an output token limit.
    estimated_tokens is a heuristic; never use it for exact billing.
    """
    if not isinstance(instructions, str) or not instructions.strip():
        raise ValueError("instructions must be nonempty")
    if not isinstance(goal, str) or not goal.strip():
        raise ValueError("goal must be nonempty")
    if type(max_chars) is not int or type(reserve_chars) is not int:
        raise ValueError("character limits must be integers")
    if reserve_chars < 0 or max_chars <= reserve_chars:
        raise ValueError("invalid character budget")
    if not isinstance(blocks, (tuple, list)):
        raise ValueError("blocks must be a list or tuple")

    blocks = tuple(blocks)
    ids = [block.source_id for block in blocks]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate source IDs risk ambiguous provenance")

    def encode(data: dict) -> str:
        return json.dumps(data, ensure_ascii=False, separators=(",", ":"), sort_keys=True)

    frame = {
        "trusted_instructions": instructions,
        "user_goal": goal,
        "untrusted_data": [],
    }
    cap = max_chars - reserve_chars
    if len(encode(frame)) > cap:
        raise ValueError("trusted goal/instructions alone exceed budget")

    selected: list[ContextBlock] = []
    dropped: list[ContextBlock] = []
    # Higher priority first, stable original order for ties.
    for _, block in sorted(enumerate(blocks), key=lambda pair: (-pair[1].priority, pair[0])):
        candidate = {
            "kind": block.kind,
            "source_id": block.source_id,
            "content": block.content,
            "trust": "untrusted",
        }
        attempt = {**frame, "untrusted_data": frame["untrusted_data"] + [candidate]}
        if len(encode(attempt)) <= cap:
            frame = attempt
            selected.append(block)
        else:
            dropped.append(block)

    payload = encode(frame)
    return PackedContext(
        payload=payload,
        selected_ids=tuple(block.source_id for block in selected),
        dropped_ids=tuple(block.source_id for block in dropped),
        estimated_tokens=math.ceil(len(payload.encode("utf-8")) / 4),
        max_chars=max_chars,
    )

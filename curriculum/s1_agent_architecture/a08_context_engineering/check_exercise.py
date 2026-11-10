import json
from exercise import solve


def main() -> None:
    result = solve({
        "goal": "Look up policy",
        "instructions": "Never transfer funds",
        "blocks": [
            {"source_id": "mem:1", "content": "user prefers concise answers"},
            {"source_id": "doc:1", "content": "X" * 1000},
        ],
        "max_chars": 300,
    })
    context = json.loads(result["context"])
    assert context["instructions"] == "Never transfer funds"
    assert context["untrusted_data"][0]["trust"] == "untrusted"
    assert result["selected_ids"] == ["mem:1"]
    assert result["dropped_ids"] == ["doc:1"]
    assert len(result["context"]) <= 300
    print("A08: PASS")


if __name__ == "__main__":
    main()

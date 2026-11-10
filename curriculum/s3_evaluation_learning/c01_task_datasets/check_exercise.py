import json
from exercise import solve


def main() -> None:
    records = [
        {"id": "a", "split": "train", "group_id": "refund", "question": "refund policy", "tags": ["policy"]},
        {"id": "b", "split": "holdout", "group_id": "shipping", "question": "shipping status", "tags": ["logistics"]},
    ]
    result = solve({"cases": records})
    assert result["count"] == 2 and result["splits"]["holdout"] == 1
    assert [json.loads(x)["id"] for x in result["jsonl"].splitlines()] == ["a", "b"]
    try:
        solve({"cases": [records[0], {**records[1], "group_id": "refund"}]})
    except ValueError as exc:
        assert "leakage" in str(exc)
    else:
        raise AssertionError("group leaking into holdout was accepted")
    print("C01: PASS")


if __name__ == "__main__":
    main()

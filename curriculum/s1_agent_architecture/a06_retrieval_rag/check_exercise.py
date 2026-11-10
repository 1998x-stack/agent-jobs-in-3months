from exercise import solve


DOCUMENTS = [
    {"id": "r1", "text": "refund needs approval from a human"},
    {"id": "s1", "text": "shipping tracking is available after dispatch"},
    {"id": "p1", "text": "password reset requires verified email"},
]


def main() -> None:
    found = solve({"documents": DOCUMENTS, "query": "refund approval", "top_k": 1})
    assert found["status"] == "ok"
    assert found["hits"][0]["doc_id"] == "r1"
    assert found["hits"][0]["score"] > 0
    assert solve({"documents": DOCUMENTS, "query": "unicorn"})["status"] == "no_evidence"
    try:
        solve({"documents": DOCUMENTS, "query": "refund", "top_k": 0})
    except ValueError:
        pass
    else:
        raise AssertionError("invalid top_k was accepted")
    print("A06: PASS")


if __name__ == "__main__":
    main()

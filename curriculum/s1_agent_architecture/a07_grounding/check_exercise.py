from exercise import solve


def main() -> None:
    base = {"evidence": {"refund:p01": "A refund needs human approval."}}
    good = solve({
        **base,
        "citation": {"chunk_id": "refund:p01", "quote": "A refund needs human approval."},
    })
    assert good["status"] == "supported" and "[refund:p01]" in good["answer"]
    for quote in ("Refunds are automatic.", "A refund needz"):
        try:
            solve({**base, "citation": {"chunk_id": "refund:p01", "quote": quote}})
        except ValueError:
            pass
        else:
            raise AssertionError("non-extractible quote was accepted")
    try:
        solve({**base, "citation": {"chunk_id": "fake:p01", "quote": "A refund needs human approval."}})
    except ValueError:
        pass
    else:
        raise AssertionError("invented source ID was accepted")
    print("A07: PASS")


if __name__ == "__main__":
    main()

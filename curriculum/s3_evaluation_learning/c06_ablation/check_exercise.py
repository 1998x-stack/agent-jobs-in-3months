from exercise import solve


def main() -> None:
    outcome = solve({
        "control": {"case-a": True, "case-b": True, "case-c": False},
        "variant": {"case-c": False, "case-b": False, "case-a": True},
        "changed_component": "retrieval_evidence",
    })
    assert outcome["delta"] == -1 / 3
    assert outcome["n"] == 3 and outcome["losses"] == 1
    try:
        solve({
            "control": {"a": True}, "variant": {"b": True},
            "changed_component": "memory",
        })
    except ValueError:
        pass
    else:
        raise AssertionError("unpaired comparison accepted")
    print("C06: PASS")


if __name__ == "__main__":
    main()

from exercise import solve


def main() -> None:
    payload = {"requester": "alice", "reviewer": "bob", "executor": "carol"}
    assert solve({**payload, "decision": "approved"})["synthetic_receipt_allowed"]
    assert not solve({**payload, "decision": "denied"})["synthetic_receipt_allowed"]
    assert not solve({**payload, "decision": "pending"})["synthetic_receipt_allowed"]
    try:
        solve({**payload, "reviewer": "alice", "decision": "approved"})
    except PermissionError:
        pass
    else:
        raise AssertionError("self-approval allowed")
    print("B07: PASS")


if __name__ == "__main__":
    main()

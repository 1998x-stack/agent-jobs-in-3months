from exercise import solve


def main() -> None:
    assert solve({"requests": [
        {"key": "key-1", "payload": {"question": "refund"}},
        {"key": "key-1", "payload": {"question": "refund"}},
        {"key": "key-2", "payload": {"question": "shipping"}},
    ]}) == {"created": 2, "replays": 1}
    try:
        solve({"requests": [
            {"key": "same", "payload": {"question": "refund"}},
            {"key": "same", "payload": {"question": "delete"}},
        ]})
    except ValueError as exc:
        assert "409" in str(exc)
    else:
        raise AssertionError("different payload reused same key")
    print("B03: PASS")


if __name__ == "__main__":
    main()

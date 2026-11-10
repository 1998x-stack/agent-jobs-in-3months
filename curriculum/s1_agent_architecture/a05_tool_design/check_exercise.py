from exercise import solve


def main() -> None:
    assert solve({"tool": "lookup_policy", "arguments": {"topic": "refund"}})["status"] == "ok"
    unknown = solve({"tool": "lookup_policy", "arguments": {"topic": "unknown"}})
    assert unknown == {"status": "no_evidence", "data": None}
    for proposal, expected in [
        ({"tool": "issue_refund", "arguments": {"topic": "refund"}}, PermissionError),
        ({"tool": "lookup_policy", "arguments": {"topic": "refund", "force": True}}, ValueError),
    ]:
        try:
            solve(proposal)
        except expected:
            pass
        else:
            raise AssertionError("invalid tool request did not fail")
    print("A05: PASS")


if __name__ == "__main__":
    main()

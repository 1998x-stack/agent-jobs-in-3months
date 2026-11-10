from exercise import solve


def main() -> None:
    attempt = {
        "expected_http": 409,
        "observed_http": 409,
        "tool_actions": ["search_policy"],
        "synthetic_receipts": 0,
        "exercised": True,
    }
    assert solve(attempt)["guard_held"]
    bad = solve({
        **attempt, "observed_http": 200,
        "tool_actions": ["search_policy", "issue_refund"],
        "synthetic_receipts": 1,
    })
    assert not bad["guard_held"] and len(bad["violations"]) == 3
    try:
        solve({**attempt, "synthetic_receipts": -1})
    except ValueError:
        pass
    else:
        raise AssertionError("negative side-effect count accepted")
    print("C04: PASS")


if __name__ == "__main__":
    main()

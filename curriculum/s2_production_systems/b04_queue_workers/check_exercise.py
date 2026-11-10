from exercise import solve


def main() -> None:
    result = solve({"jobs": ["a", "b", "c", "d"], "workers": 4})
    assert result == {
        "jobs": 4,
        "claims": 4,
        "unique_claims": 4,
        "no_duplicate_claim": True,
    }
    try:
        solve({"jobs": ["job"], "workers": 0})
    except ValueError:
        pass
    else:
        raise AssertionError("unbounded invalid worker count")
    print("B04: PASS")


if __name__ == "__main__":
    main()

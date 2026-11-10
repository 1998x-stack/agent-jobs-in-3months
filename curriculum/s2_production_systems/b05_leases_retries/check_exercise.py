from exercise import solve


def main() -> None:
    value = solve({"lease_seconds": 5, "retry_attempt": 2})
    assert value["stale_committed"] is False
    assert value["fresh_committed"] is True
    assert value["backoff_seconds"] == 4
    assert solve({"retry_attempt": 3})["final_attempt"] is True
    try:
        solve({"lease_seconds": -1})
    except ValueError:
        pass
    else:
        raise AssertionError("invalid lease accepted")
    print("B05: PASS")


if __name__ == "__main__":
    main()

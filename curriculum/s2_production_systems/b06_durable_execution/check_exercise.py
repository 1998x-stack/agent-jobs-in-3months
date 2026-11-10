from exercise import solve


def main() -> None:
    recovered = solve({"steps": ["plan", "research", "review"], "crash_after": 2})
    assert recovered == {
        "reused": ["plan", "research"], "executed": ["review"], "total": 3,
    }
    assert solve({"steps": ["plan", "review"], "crash_after": 0})["reused"] == []
    try:
        solve({"steps": ["plan", "plan"], "crash_after": 1})
    except ValueError:
        pass
    else:
        raise AssertionError("duplicate checkpoint IDs were accepted")
    print("B06: PASS")


if __name__ == "__main__":
    main()

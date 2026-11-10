from exercise import solve


def main() -> None:
    assert solve({}) == {"committed": True, "runs": 1, "audits": 1}
    assert solve({"fail_audit": True}) == {"committed": False, "runs": 0, "audits": 0}
    try:
        solve({"fail_audit": "true"})
    except ValueError:
        pass
    else:
        raise AssertionError("invalid failure type accepted")
    print("B02: PASS")


if __name__ == "__main__":
    main()

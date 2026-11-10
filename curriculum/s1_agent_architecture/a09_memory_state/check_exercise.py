from exercise import solve


def main() -> None:
    result = solve({
        "tenant": "tenant-a", "user": "user-a",
        "key": "preference", "value": "English",
    })
    assert result["value"] == "English"
    assert result["other_tenant_value"] is None
    try:
        solve({"tenant": "tenant-a", "user": "", "key": "x", "value": "y"})
    except ValueError:
        pass
    else:
        raise AssertionError("missing user scope was allowed")
    print("A09: PASS")


if __name__ == "__main__":
    main()

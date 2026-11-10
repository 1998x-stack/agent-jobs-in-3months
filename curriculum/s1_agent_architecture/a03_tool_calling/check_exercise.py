from exercise import solve

def main():
    assert "approval" in solve({
        "tool": "lookup_policy", "arguments": {"topic": "refund"}
    })["result"]
    for data, error in [
        ({"tool": "delete_all", "arguments": {"topic": "refund"}}, PermissionError),
        ({"tool": "lookup_policy", "arguments": {"topic": "refund", "admin": True}}, ValueError),
    ]:
        try:
            solve(data)
        except error:
            pass
        else:
            raise AssertionError("unsafe tool proposal accepted")
    print("A03: PASS")

if __name__ == "__main__":
    main()

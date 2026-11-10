from exercise import solve


def main() -> None:
    args = {
        "actor_tenant": "team-a", "target_tenant": "team-a",
        "role": "viewer", "permission": "runs:read",
    }
    assert solve(args)["authorized"]
    for malicious in (
        {**args, "target_tenant": "team-b"},
        {**args, "permission": "approvals:execute"},
        {**args, "role": "unknown"},
    ):
        try:
            solve(malicious)
        except PermissionError:
            pass
        else:
            raise AssertionError("unauthorized action permitted")
    print("B08: PASS")


if __name__ == "__main__":
    main()

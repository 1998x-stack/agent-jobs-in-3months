from exercise import solve


def main() -> None:
    args = {
        "required_tools": ["search_policy", "verify_quote"],
        "forbidden_tools": ["issue_refund"],
        "trace": [
            {"name": "search_policy", "args": {"top_k": 3}},
            {"name": "verify_quote", "args": {}},
        ],
        "expected_parameter": {"tool": "search_policy", "key": "top_k", "value": 3},
    }
    assert solve(args)["passed"]
    assert not solve({**args, "trace": list(reversed(args["trace"]))})["required_ok"]
    assert not solve({**args, "trace": args["trace"] + [{"name": "issue_refund", "args": {}}]})["safety_ok"]
    assert not solve({**args, "trace": [{"name": "search_policy", "args": None}, args["trace"][1]]})["parameters_ok"]
    print("C03: PASS")


if __name__ == "__main__":
    main()

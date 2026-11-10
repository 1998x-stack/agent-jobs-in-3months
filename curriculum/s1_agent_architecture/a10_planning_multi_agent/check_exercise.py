from exercise import solve


def main() -> None:
    result = solve({"goal": "refund approval and refund timeline", "max_tasks": 2})
    assert result["task_count"] == 2
    assert len(result["handoffs"]) == 4
    assert result["handoffs"][0] == {
        "task_id": "task-01", "from": "planner", "to": "researcher"
    }
    try:
        solve({"goal": "one and two and three", "max_tasks": 2})
    except RuntimeError:
        pass
    else:
        raise AssertionError("excess tasks were allowed")
    print("A10: PASS")


if __name__ == "__main__":
    main()

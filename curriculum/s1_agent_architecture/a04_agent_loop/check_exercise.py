from exercise import solve

def main():
    value = solve({"goal": "Explain refund policy", "max_steps": 2})
    assert value["stop_reason"] == "finished"
    assert len(value["trace"]) == 1
    try:
        solve({"goal": "Explain refund policy", "max_steps": 1})
    except RuntimeError:
        pass
    else:
        raise AssertionError("budget must stop loop")
    try:
        solve({"goal": "x", "actions": [{"kind": "tool", "name": "delete_all"}]})
    except PermissionError:
        pass
    else:
        raise AssertionError("unsafe tool accepted")
    print("A04: PASS")

if __name__ == "__main__":
    main()

from exercise import solve


def main() -> None:
    rows = [
        {"case_id": "a", "control": False, "variant": True},
        {"case_id": "b", "control": True, "variant": True},
        {"case_id": "c", "control": True, "variant": False},
        {"case_id": "d", "control": False, "variant": True},
    ]
    a = solve({"pairs": rows, "samples": 500, "seed": 11})
    b = solve({"pairs": list(reversed(rows)), "samples": 500, "seed": 11})
    assert a == b
    assert a["delta"] == 0.25 and a["wins"] == 2 and a["losses"] == 1
    assert a["small_sample"] is True
    try:
        solve({"pairs": rows + [rows[0]]})
    except ValueError:
        pass
    else:
        raise AssertionError("duplicate case ID accepted")
    print("C05: PASS")


if __name__ == "__main__":
    main()

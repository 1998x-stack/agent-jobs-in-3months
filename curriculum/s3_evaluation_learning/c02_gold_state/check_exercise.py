from exercise import solve


def main() -> None:
    gold = {"run_status": "completed", "result_status": "supported", "receipt_count": 0}
    actual = {**gold, "final_text": "I have issued a refund!"}
    assert solve({"expected": gold, "actual": actual})["passed"]
    wrong = {**actual, "receipt_count": 1}
    assert solve({"expected": gold, "actual": wrong})["mismatches"] == ["receipt_count"]
    print("C02: PASS")


if __name__ == "__main__":
    main()

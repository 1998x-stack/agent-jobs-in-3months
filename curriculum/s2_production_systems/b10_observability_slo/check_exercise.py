from exercise import solve


def main() -> None:
    good = solve({
        "samples": [{"duration_ms": index, "ok": True} for index in range(1, 21)],
        "min_samples": 20,
        "p95_target_ms": 19,
    })
    assert good["p95_latency_ms"] == 19
    assert good["slo_status"] == "met"
    failure = solve({
        "samples": [{"duration_ms": 10, "ok": False}],
        "min_samples": 1,
    })
    assert failure["slo_status"] == "breached"
    with_small_sample = solve({
        "samples": [{"duration_ms": 2, "ok": True}],
    })
    assert with_small_sample["slo_status"] == "insufficient_samples"
    print("B10: PASS")


if __name__ == "__main__":
    main()

"""C04–C06 offline safety + paired-statistics + ablation experiment demo.

Synthetic fixtures only. CLI gates observed guard checks and predictable
read-only component dependencies, never real-world model robustness.
"""
import argparse
import json

from .ablation_lab import evaluate_ablations
from .safety_eval import default_dataset, evaluate_safety


def main() -> None:
    parser = argparse.ArgumentParser(description="Synthetic C04-C06 evaluation")
    parser.add_argument("--safety-dataset", default=str(default_dataset()))
    parser.add_argument("--bootstrap-samples", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--assert-pass", action="store_true")
    args = parser.parse_args()
    safety = evaluate_safety(args.safety_dataset)
    ablation = evaluate_ablations(
        bootstrap_samples=args.bootstrap_samples, seed=args.seed,
    )
    report = {
        "schema_version": "agent-science-report.v1",
        "safety": safety,
        "ablation": ablation,
    }
    print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
    if args.assert_pass:
        variations = ablation["variants"]
        if (
            safety["violations"] != 0
            or ablation["control_passed"] != ablation["n_cases"]
            or variations["empty_retrieval"]["paired"]["variant_successes"]
                >= variations["empty_retrieval"]["paired"]["control_successes"]
            or variations["no_decomposition"]["paired"]["variant_successes"]
                >= variations["no_decomposition"]["paired"]["control_successes"]
        ):
            raise SystemExit("C04-C06 offline regression gate failed")


if __name__ == "__main__":
    main()


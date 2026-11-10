"""Offline P3 benchmark CLI. Holdout is synthetic, not real-world accuracy.

Example:
 PYTHONPATH=projects/p1_agent_harness/src:projects/p2_cloud_runtime/src:projects/p3_eval_learning_lab/src python -m agent_eval.benchmark_demo --split holdout --assert-pass
"""
import argparse
import json
from pathlib import Path

from .eval_pipeline import evaluate


def default_dataset() -> Path:
    return Path(__file__).resolve().parents[4] / "datasets" / "agent_eval_v1.jsonl"


def main() -> None:
    parser = argparse.ArgumentParser(description="Synthetic offline agent evaluation")
    parser.add_argument("--dataset", type=Path, default=default_dataset())
    parser.add_argument("--split", choices=("train", "dev", "holdout"))
    parser.add_argument("--assert-pass", action="store_true", help="CI regression gate")
    args = parser.parse_args()
    report = evaluate(args.dataset, split=args.split)
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    if args.assert_pass and report["passed"] != report["n"]:
        raise SystemExit("Offline regression failed")


if __name__ == "__main__":
    main()


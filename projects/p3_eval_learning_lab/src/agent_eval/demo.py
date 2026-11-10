"""Run: PYTHONPATH=projects/p3_eval_learning_lab/src python -m agent_eval.demo"""
from pathlib import Path
from .cases import load_cases
from .experiments import compare
from .dpo_math import dpo_loss

def main() -> None:
    data = Path(__file__).resolve().parents[4] / "datasets" / "synthetic_cases.jsonl"
    cases = load_cases(data)
    print("Offline ablation:", compare(cases))
    print("DPO loss illustration:", round(dpo_loss(1.2, -0.3), 6))

if __name__ == "__main__":
    main()

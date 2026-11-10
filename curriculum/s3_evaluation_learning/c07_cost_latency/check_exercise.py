"""Run directly: python curriculum/s3_evaluation_learning/c07_cost_latency/check_exercise.py"""
from exercise import solve

def main() -> None:
    # Replace this generic contract with an actual edge-case assertion.
    result = solve({"goal": "minimal reproducible learning task"})
    assert isinstance(result, dict), "Return a structured result"
    print("C07 baseline check passed; add boundary cases next")

if __name__ == "__main__":
    main()

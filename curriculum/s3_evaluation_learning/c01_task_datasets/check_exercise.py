"""Run directly: python curriculum/s3_evaluation_learning/c01_task_datasets/check_exercise.py"""
from exercise import solve

def main() -> None:
    # Replace this generic contract with an actual edge-case assertion.
    result = solve({"goal": "minimal reproducible learning task"})
    assert isinstance(result, dict), "Return a structured result"
    print("C01 baseline check passed; add boundary cases next")

if __name__ == "__main__":
    main()

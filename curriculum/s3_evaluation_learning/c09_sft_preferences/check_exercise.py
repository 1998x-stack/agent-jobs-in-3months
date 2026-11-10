"""Run directly: python curriculum/s3_evaluation_learning/c09_sft_preferences/check_exercise.py"""
from exercise import solve

def main() -> None:
    # Replace this generic contract with an actual edge-case assertion.
    result = solve({"goal": "minimal reproducible learning task"})
    assert isinstance(result, dict), "Return a structured result"
    print("C09 baseline check passed; add boundary cases next")

if __name__ == "__main__":
    main()

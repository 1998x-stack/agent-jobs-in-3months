"""Run directly: python curriculum/s1_agent_architecture/a08_context_engineering/check_exercise.py"""
from exercise import solve

def main() -> None:
    # Replace this generic contract with an actual edge-case assertion.
    result = solve({"goal": "minimal reproducible learning task"})
    assert isinstance(result, dict), "Return a structured result"
    print("A08 baseline check passed; add boundary cases next")

if __name__ == "__main__":
    main()

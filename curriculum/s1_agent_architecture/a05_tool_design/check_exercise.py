"""Run directly: python curriculum/s1_agent_architecture/a05_tool_design/check_exercise.py"""
from exercise import solve

def main() -> None:
    # Replace this generic contract with an actual edge-case assertion.
    result = solve({"goal": "minimal reproducible learning task"})
    assert isinstance(result, dict), "Return a structured result"
    print("A05 baseline check passed; add boundary cases next")

if __name__ == "__main__":
    main()

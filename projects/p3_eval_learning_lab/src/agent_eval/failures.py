"""Simple first-failure categorizer. Expand to richer trace mining."""
def classify(result: dict) -> str:
    if not result.get("safety_ok", True):
        return "safety"
    if not result.get("trajectory_ok", True):
        return "trajectory"
    if not result.get("outcome_ok", True):
        return "outcome"
    return "passed"

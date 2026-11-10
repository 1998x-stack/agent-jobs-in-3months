"""Deterministic offline planner; replace with a validated LLM adapter later."""
from .models import Action

class LookupThenFinish:
    def decide(self, state: dict) -> Action:
        if not state["observations"]:
            return Action(kind="tool", name="lookup_policy",
                          arguments={"topic": state["goal"]})
        return Action(kind="finish",
                      output=str(state["observations"][-1]["result"]))

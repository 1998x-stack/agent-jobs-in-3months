"""Safe trace formatting; production telemetry and redaction are TODO."""
from .models import AgentResult

def summarize(result: AgentResult) -> list[str]:
    # Do not log raw prompts, secrets or unredacted user data in production.
    return [f"step={step.step} tool={step.action}" for step in result.trace]

"""A04: an explicit Responses API agent loop with controlled read-only tools."""
from .llm import (
    AgentBudgetExceeded,
    ModelAdapter,
    ModelProtocolError,
    ToolFeedback,
)
from .models import AgentResult, TraceStep
from .typed_tools import ValidatedToolRegistry


def run_live_agent(
    goal: str,
    adapter: ModelAdapter,
    tools: ValidatedToolRegistry,
    *,
    max_model_turns: int = 6,
    max_tool_calls: int = 4,
) -> AgentResult:
    if not goal.strip():
        raise ValueError("goal must not be blank")
    if max_model_turns <= 0 or max_tool_calls < 0:
        raise ValueError("invalid execution budget")
    response_id: str | None = None
    feedback: ToolFeedback | None = None
    trace: list[TraceStep] = []
    for turn_number in range(1, max_model_turns + 1):
        turn = adapter.create_turn(
            goal=goal if response_id is None else None,
            feedback=feedback,
            previous_response_id=response_id,
            tool_definitions=tools.definitions(),
        )
        if not turn.response_id:
            raise ModelProtocolError("model returned an empty response id")
        if len(turn.tool_calls) > 1:
            raise ModelProtocolError("multiple tool calls are not supported")
        if not turn.tool_calls:
            if not turn.final_text or not turn.final_text.strip():
                raise ModelProtocolError("missing final text")
            return AgentResult(output=turn.final_text, trace=trace)
        if len(trace) >= max_tool_calls:
            # The proposed tool is NEVER executed if the budget has run out.
            raise AgentBudgetExceeded("tool call budget exhausted")
        call = turn.tool_calls[0]
        if not call.call_id:
            raise ModelProtocolError("missing function call id")
        output = tools.execute(call)
        # Trace contains metadata only; never accidentally log sensitive tool results.
        trace.append(TraceStep(
            step=turn_number,
            action=call.name,
            observation={"status": "ok", "response_id": turn.response_id},
        ))
        response_id = turn.response_id
        feedback = ToolFeedback(call_id=call.call_id, output=output)
    raise AgentBudgetExceeded("model turn budget exhausted")

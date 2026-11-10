"""A01-A04 integration tests: fake Responses client, zero network requests."""
from types import SimpleNamespace as Obj
import json

import pytest

from agent_harness.live_demo import build_read_only_tools
from agent_harness.live_loop import run_live_agent
from agent_harness.llm import AgentBudgetExceeded, ModelProtocolError, ToolProposal
from agent_harness.openai_adapter import OpenAIResponsesAdapter
from agent_harness.typed_tools import InvalidToolArguments


def response(response_id="r1", *, calls=None, text="", status="completed", usage=None):
    return Obj(
        id=response_id,
        status=status,
        output=calls or [],
        output_text=text,
        usage=Obj(input_tokens=10, output_tokens=6) if usage is None else usage,
    )


def tool_call(name="lookup_policy", args='{"topic":"refund"}', call_id="call_1"):
    return Obj(type="function_call", name=name, arguments=args, call_id=call_id)


class FakeResponses:
    def __init__(self, replies):
        self.replies = list(replies)
        self.requests = []

    def create(self, **kwargs):
        self.requests.append(kwargs)
        return self.replies.pop(0)


class FakeClient:
    def __init__(self, replies):
        self.responses = FakeResponses(replies)


def adapter_with(*replies):
    client = FakeClient(replies)
    return OpenAIResponsesAdapter(client=client, model="test-model"), client


def test_two_turn_model_tool_model_roundtrip():
    adapter, client = adapter_with(
        response("r1", calls=[tool_call()]),
        response("r2", text="Refund needs policy checks and human approval."),
    )
    result = run_live_agent("Look up refund policy", adapter, build_read_only_tools())
    assert "human approval" in result.output
    assert [step.action for step in result.trace] == ["lookup_policy"]
    assert result.trace[0].observation["status"] == "ok"

    first, second = client.responses.requests
    assert first["model"] == "test-model"
    assert first["input"] == [{"role": "user", "content": "Look up refund policy"}]
    assert first["parallel_tool_calls"] is False
    assert first["max_output_tokens"] == 1024
    assert first["store"] is True
    assert "previous_response_id" not in first
    assert second["previous_response_id"] == "r1"
    assert second["input"][0]["type"] == "function_call_output"
    assert second["input"][0]["call_id"] == "call_1"
    assert json.loads(second["input"][0]["output"])["result"].startswith("Refunds")


def test_strict_schema_and_local_pydantic_validation():
    tool = build_read_only_tools().definitions()[0]
    assert tool["name"] == "lookup_policy"
    assert tool["strict"] is True
    assert tool["parameters"]["additionalProperties"] is False
    assert tool["parameters"]["required"] == ["topic"]
    tools = build_read_only_tools()
    with pytest.raises(InvalidToolArguments):
        tools.execute(ToolProposal("1", "lookup_policy", '{"topic":"refund","admin":true}'))
    with pytest.raises(InvalidToolArguments):
        tools.execute(ToolProposal("1", "lookup_policy", '{"topic":42}'))
    with pytest.raises(InvalidToolArguments):
        tools.execute(ToolProposal("1", "lookup_policy", '{"topic":""}'))
    with pytest.raises(InvalidToolArguments):
        tools.execute(ToolProposal("1", "lookup_policy", '["refund"]'))
    with pytest.raises(InvalidToolArguments):
        tools.execute(ToolProposal("1", "lookup_policy", "{malformed"))


def test_unknown_tool_and_write_tool_never_run():
    adapter, _ = adapter_with(response(calls=[tool_call(name="transfer_funds")]))
    with pytest.raises(PermissionError):
        run_live_agent("lookup", adapter, build_read_only_tools())
    assert build_read_only_tools().definitions()[0]["name"] == "lookup_policy"


def test_tool_budget_blocks_model_suggestion_before_execution():
    adapter, client = adapter_with(response(calls=[tool_call()]))
    with pytest.raises(AgentBudgetExceeded, match="tool call budget"):
        run_live_agent("lookup", adapter, build_read_only_tools(), max_tool_calls=0)
    assert len(client.responses.requests) == 1


def test_model_turn_limit_catches_loops():
    adapter, client = adapter_with(response(calls=[tool_call()]))
    with pytest.raises(AgentBudgetExceeded, match="model turn budget"):
        run_live_agent("lookup", adapter, build_read_only_tools(), max_model_turns=1)
    assert len(client.responses.requests) == 1


@pytest.mark.parametrize("bad_reply", [
    response(status="incomplete", text="partial"),
    response(text=""),
    response(calls=[tool_call(), tool_call(call_id="call2")]),
    response(response_id="", text="answer"),
])
def test_invalid_responses_fail_closed(bad_reply):
    adapter, _ = adapter_with(bad_reply)
    with pytest.raises(ModelProtocolError):
        run_live_agent("lookup", adapter, build_read_only_tools())


def test_adapter_does_not_accept_feedback_without_previous_response_id():
    adapter, _ = adapter_with()
    from agent_harness.llm import ToolFeedback
    with pytest.raises(ValueError):
        adapter.create_turn(
            goal=None,
            feedback=ToolFeedback("x", "ok"),
            previous_response_id=None,
            tool_definitions=[],
        )


def test_no_secret_output_in_trace():
    from agent_harness.typed_tools import ValidatedToolRegistry
    from agent_harness.schemas import PolicyLookupArgs
    tools = ValidatedToolRegistry()
    tools.register("lookup_policy", "testing", PolicyLookupArgs, lambda topic: "SECRET")
    adapter, _ = adapter_with(
        response(calls=[tool_call()]), response("r2", text="Safe final answer")
    )
    result = run_live_agent("lookup", adapter, tools)
    assert "SECRET" not in repr(result.trace)


def test_read_only_guards_write_capabilities():
    from agent_harness.typed_tools import ValidatedToolRegistry
    from agent_harness.schemas import PolicyLookupArgs
    tools = ValidatedToolRegistry()
    calls = []
    tools.register(
        "dangerous_write", "do not offer this", PolicyLookupArgs,
        lambda **kwargs: calls.append(kwargs),
        read_only=False,
    )
    assert tools.definitions() == []
    with pytest.raises(PermissionError):
        tools.execute(ToolProposal("1", "dangerous_write", '{"topic":"refund"}'))
    assert calls == []

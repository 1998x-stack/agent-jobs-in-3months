"""A05-A07 tests: file retrieval, evidence verification, and model-tool loop."""
import json

import pytest

from agent_harness.grounding import (
    NO_EVIDENCE_MESSAGE, UnverifiedAnswer, run_grounded_agent,
    verify_extractive_answer,
)
from agent_harness.llm import ModelTurn, ToolProposal
from agent_harness.policy_search import PolicyCorpus, demo_corpus
from agent_harness.retrieval_eval import evaluate, load_cases
from agent_harness.retrieval_tools import RetrievalSession, SearchPolicyArgs
from agent_harness.typed_tools import InvalidToolArguments


def test_document_chunks_have_stable_source_ids():
    chunks = [c for c in demo_corpus().chunks if c.document_id == "refund_approval"]
    assert [c.chunk_id for c in chunks] == ["refund_approval:p01", "refund_approval:p02"]
    assert all(c.source == "datasets/policy_docs/refund_approval.md" for c in chunks)


def test_bm25_retrieves_expected_policy_chunk():
    hits = demo_corpus().search(
        "refund proposal transfer money human approval", tenant="public-demo", top_k=2
    )
    assert hits and hits[0].chunk.chunk_id == "refund_approval:p01"
    assert hits[0].score > 0


def test_unknown_query_returns_no_evidence_not_fabrication():
    assert demo_corpus().search("galactic unicorn spaceship", tenant="public-demo") == []
    session = RetrievalSession(demo_corpus(), tenant="public-demo")
    assert session.search_policy(query="galactic unicorn spaceship", top_k=3) == {
        "status": "no_evidence", "hits": []
    }


def test_tenant_scope_is_bound_to_server():
    corpus = demo_corpus()
    query = "Tenant Alpha billing reconciliation Wednesday"
    assert any(
        hit.chunk.document_id == "tenant_alpha_billing"
        for hit in corpus.search(query, tenant="tenant-alpha")
    )
    assert all(
        hit.chunk.document_id != "tenant_alpha_billing"
        for hit in corpus.search(query, tenant="tenant-beta")
    )
    assert "tenant" not in SearchPolicyArgs.model_json_schema()["properties"]
    session = RetrievalSession(corpus, tenant="tenant-beta")
    assert all(
        hit["chunk_id"] != "tenant_alpha_billing:p01"
        for hit in session.search_policy(query=query, top_k=5)["hits"]
    )


def test_manifest_rejects_path_traversal(tmp_path):
    (tmp_path / "outside.md").write_text("secret", encoding="utf-8")
    folder = tmp_path / "docs"
    folder.mkdir()
    (folder / "index.json").write_text(json.dumps([{
        "id": "malicious", "title": "bad", "file": "../outside.md", "scope": "public",
    }]), encoding="utf-8")
    with pytest.raises(ValueError, match="local Markdown"):
        PolicyCorpus.from_directory(folder)


def test_typed_search_tool_contract_and_errors():
    session = RetrievalSession(demo_corpus(), tenant="public-demo")
    tools = session.registry()
    definition = tools.definitions()[0]
    assert definition["strict"] is True
    assert definition["parameters"]["additionalProperties"] is False
    assert set(definition["parameters"]["required"]) == {"query", "top_k"}
    output = json.loads(tools.execute(ToolProposal(
        "call_1", "search_policy",
        '{"query":"refund proposal human approval","top_k":2}'
    )))["result"]
    assert output["status"] == "ok"
    assert output["hits"][0]["chunk_id"] in session.evidence
    with pytest.raises(InvalidToolArguments):
        tools.execute(ToolProposal(
            "call_2", "search_policy",
            '{"query":"refund","top_k":3,"tenant":"tenant-alpha"}'
        ))
    with pytest.raises(InvalidToolArguments):
        tools.execute(ToolProposal("call_3", "search_policy", '{"query":"refund","top_k":99}'))
    with pytest.raises(PermissionError):
        tools.execute(ToolProposal("call_4", "delete_payments", "{}"))


def test_verifier_accepts_exact_excerpts():
    chunk = next(c for c in demo_corpus().chunks if c.chunk_id == "refund_approval:p01")
    payload = {
        "status": "supported",
        "citations": [{"chunk_id": chunk.chunk_id, "quote": chunk.text}],
    }
    answer = verify_extractive_answer(json.dumps(payload), {chunk.chunk_id: chunk})
    assert answer.status == "supported"
    assert answer.citation_ids == (chunk.chunk_id,)
    assert chunk.text in answer.text and chunk.source in answer.text


@pytest.mark.parametrize("payload", [
    {"status": "supported", "citations": [{"chunk_id": "made_up:p01", "quote": "A refund proposal is a draft request."}]},
    {"status": "supported", "citations": [{"chunk_id": "refund_approval:p01", "quote": "All refunds are automatic and instant."}]},
    {"status": "supported", "citations": []},
    {"status": "supported", "citations": [{"chunk_id": "refund_approval:p01", "quote": "A refund proposal is a draft request."}], "summary": "Unverified summary"},
    {"status": "insufficient_evidence", "citations": [{"chunk_id": "refund_approval:p01", "quote": "A refund proposal is a draft request."}]},
])
def test_verifier_rejects_unsupported_content(payload):
    chunk = next(c for c in demo_corpus().chunks if c.chunk_id == "refund_approval:p01")
    with pytest.raises(UnverifiedAnswer):
        verify_extractive_answer(json.dumps(payload), {chunk.chunk_id: chunk})


def test_abstention_is_explicit():
    answer = verify_extractive_answer(
        '{"status":"insufficient_evidence","citations":[]}', {}
    )
    assert answer.text == NO_EVIDENCE_MESSAGE


class TwoTurnFakeModel:
    def __init__(self, query):
        self.query = query
        self.calls = 0

    def create_turn(self, *, goal, feedback, previous_response_id, tool_definitions):
        self.calls += 1
        if previous_response_id is None:
            assert feedback is None
            assert tool_definitions[0]["name"] == "search_policy"
            return ModelTurn(
                response_id="r1",
                tool_calls=(ToolProposal(
                    "call_1", "search_policy",
                    json.dumps({"query": self.query, "top_k": 3}),
                ),),
            )
        assert previous_response_id == "r1" and feedback.call_id == "call_1"
        data = json.loads(feedback.output)["result"]
        if data["status"] == "no_evidence":
            final = {"status": "insufficient_evidence", "citations": []}
        else:
            hit = data["hits"][0]
            final = {"status": "supported", "citations": [{
                "chunk_id": hit["chunk_id"], "quote": hit["text"]
            }]}
        return ModelTurn(response_id="r2", final_text=json.dumps(final))


def test_grounded_agent_model_tool_model_roundtrip():
    model = TwoTurnFakeModel("refund proposal transfer money human approval")
    result = run_grounded_agent(
        "Does a refund proposal transfer money?", model, demo_corpus(),
        tenant="public-demo",
    )
    assert result.answer.status == "supported"
    assert result.answer.citation_ids == ("refund_approval:p01",)
    assert result.trace[0].action == "search_policy"
    assert model.calls == 2


def test_grounded_agent_can_abstain_when_document_missing():
    model = TwoTurnFakeModel("galactic unicorn spaceship")
    result = run_grounded_agent(
        "When does the spaceship launch?", model, demo_corpus(),
        tenant="public-demo",
    )
    assert result.answer.status == "insufficient_evidence"
    assert result.answer.text == NO_EVIDENCE_MESSAGE


def test_retrieval_evaluation_returns_reproducible_metrics():
    from pathlib import Path
    repo = Path(__file__).resolve().parents[3]
    cases = load_cases(repo / "datasets" / "retrieval_cases.jsonl")
    result = evaluate(demo_corpus(), cases, top_k=3)
    assert result["n"] == 13
    assert result["positive_cases"] == 11
    assert result["negative_cases"] == 2
    assert result["recall_at_k"] >= 0.9
    assert result["mrr_at_k"] >= 0.75
    assert result["no_evidence_accuracy"] == 1.0

"""C01-C03 contract, actual P1/P2 replay, gold-state, trajectory/failure tests."""
from dataclasses import replace
import json
from pathlib import Path

from pydantic import ValidationError
import pytest

from agent_harness.agent_team import OfflineResearchAdapter
from agent_harness.grounding import run_grounded_agent
from agent_harness.models import AgentResult
from agent_harness.policy_search import demo_corpus
from agent_harness.scoped_memory import MemoryScope
from agent_runtime.run_repository import RunRepository

from agent_eval.contracts import (
    EvalCase, GoldState, ToolConstraint, benchmark_digest, coverage, load_benchmark,
)
from agent_eval.eval_pipeline import evaluate, replay_case
from agent_eval.state_oracle import ObservedState, grade_state, observe_state
from agent_eval.taxonomy import diagnose
from agent_eval.trajectory import (
    TraceEvent, from_p1_result, from_p2_run, grade_trajectory,
)


ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "datasets" / "agent_eval_v1.jsonl"


def cases():
    return load_benchmark(DATA)


def test_dataset_has_versioned_split_and_document_group_separation():
    dataset = cases()
    assert len(dataset) == 13
    stats = coverage(dataset)
    assert stats["splits"] == {"dev": 4, "holdout": 5, "train": 4}
    assert len(stats["digest_sha256"]) == 64
    assert benchmark_digest(dataset) == benchmark_digest(tuple(reversed(dataset)))
    assert all(case.schema_version == "agent-eval.v1" for case in dataset)
    assert all(case.tenant and case.question and case.tags for case in dataset)


def test_dataset_rejects_invalid_json_unknown_fields_and_duplicate_ids(tmp_path):
    case = cases()[0]
    path = tmp_path / "invalid.jsonl"
    path.write_text(case.model_dump_json() + "\n{bad json\n")
    with pytest.raises(ValueError, match="line 2"):
        load_benchmark(path)
    bad = case.model_dump()
    bad["password"] = "do-not-store-this"
    path.write_text(json.dumps(bad) + "\n")
    with pytest.raises(ValueError, match="line 1"):
        load_benchmark(path)
    path.write_text(case.model_dump_json() + "\n" + case.model_dump_json())
    with pytest.raises(ValueError, match="duplicate case"):
        load_benchmark(path)


def test_dataset_rejects_cross_split_group_and_exact_duplicate_question(tmp_path):
    base = cases()[0]
    alternative = cases()[4]
    cross_group = alternative.model_copy(
        update={"split": "holdout", "group_id": base.group_id}
    )
    path = tmp_path / "leak.jsonl"
    path.write_text(base.model_dump_json() + "\n" + cross_group.model_dump_json())
    with pytest.raises(ValueError, match="group contamination"):
        load_benchmark(path)
    question_leak = alternative.model_copy(
        update={"split": "holdout", "question": base.question}
    )
    path.write_text(base.model_dump_json() + "\n" + question_leak.model_dump_json())
    with pytest.raises(ValueError, match="question contamination"):
        load_benchmark(path)


def test_gold_model_rejects_inconsistent_abstention():
    with pytest.raises(ValidationError):
        GoldState(
            run_status="completed",
            result_status="insufficient_evidence",
            required_citations=["refund_approval:p01"],
        )
    with pytest.raises(ValidationError):
        GoldState(run_status="failed", result_status="supported")


def test_oracle_detects_text_success_without_database_success():
    gold = cases()[0].gold
    actual = ObservedState(
        run_status="failed", result_status=None,
        citation_ids=(), checkpoint_keys=(), receipt_count=0,
    )
    result = grade_state(gold, actual)
    assert not result.passed
    assert "run_status_ok" in result.failure_codes
    assert "citations_ok" in result.failure_codes


def test_oracle_detects_side_effect_and_abstention_citation():
    case = next(c for c in cases() if c.scenario == "abstention")
    observed = ObservedState(
        run_status="completed", result_status="insufficient_evidence",
        citation_ids=("refund_approval:p01",),
        checkpoint_keys=("plan", "task-01"),
        receipt_count=1,
    )
    result = grade_state(case.gold, observed)
    assert not result.passed
    assert result.checks["receipt_count_ok"] is False
    assert result.checks["citations_ok"] is False


def test_p1_adapter_reads_actual_trace_without_exposing_observations():
    question = "refund proposal transfer money human approval"
    response = run_grounded_agent(
        question, OfflineResearchAdapter(question), demo_corpus(),
        tenant="public-demo",
    )
    assert response.answer.status == "supported"
    wrapped = AgentResult(output="private-model-output-do-not-log", trace=response.trace)
    events = from_p1_result(wrapped)
    assert len(events) == 1
    assert events[0].name == "search_policy"
    assert events[0].arguments is None
    assert "private-model-output" not in events[0].model_dump_json()
    assert "refund" not in events[0].model_dump_json()


def test_trajectory_args_unknown_fails_closed():
    case = cases()[0].model_copy(update={
        "required_tool_arguments": [
            ToolConstraint(name="search_policy", arguments_subset={"top_k": 3})
        ]
    })
    observed = [
        TraceEvent(index=1, kind="checkpoint", name="plan", origin="p2_checkpoint"),
        TraceEvent(index=2, kind="tool_call", name="search_policy", origin="p2_checkpoint"),
        TraceEvent(index=3, kind="checkpoint", name="task-01", origin="p2_checkpoint"),
        TraceEvent(index=4, kind="run_state", name="completed", origin="p2_run_state"),
    ]
    score = grade_trajectory(case, observed)
    assert not score.passed
    assert "tool_arguments_ok" in score.failure_codes
    assert score.arguments_observed is False
    observed[1] = observed[1].model_copy(update={"arguments": {"top_k": 3}})
    assert grade_trajectory(case, observed).passed
    observed[1] = observed[1].model_copy(update={"arguments": {"top_k": 5}})
    assert not grade_trajectory(case, observed).passed


def test_forbidden_tool_and_bad_event_index_have_deterministic_failures():
    case = cases()[0]
    tool = TraceEvent(index=1, kind="tool_call", name="issue_refund", origin="p1_agent_loop")
    result = grade_trajectory(case, [tool])
    assert not result.passed
    assert result.checks["forbidden_tools_ok"] is False
    assert "forbidden_tools_ok" in result.failure_codes
    with pytest.raises(ValidationError):
        TraceEvent(
            index=1, kind="tool_call", name="search_policy",
            origin="p1_agent_loop", raw_prompt="this-must-not-be-stored",
        )
    unordered = [
        TraceEvent(index=2, kind="checkpoint", name="plan", origin="p2_checkpoint")
    ]
    assert not grade_trajectory(case, unordered).checks["trace_structure_ok"]


def test_taxonomy_prefers_safety_over_secondary_outcome_failure():
    case = cases()[0]
    state = grade_state(case.gold, ObservedState(
        "failed", None, (), (), 0,
    ))
    process = grade_trajectory(case, [
        TraceEvent(index=1, kind="tool_call", name="issue_refund", origin="p1_agent_loop"),
    ])
    report = diagnose(state, process)
    assert report.primary == "unsafe_tool"
    assert "wrong_run_state" in report.all_failure_codes


def test_actual_p2_persisted_trace_and_actor_isolation(tmp_path):
    repo = RunRepository(tmp_path / "evidence.sqlite3")
    scope = MemoryScope("public-demo", "synthetic")
    run, _ = repo.submit(
        scope, idempotency_key="actual-trace-0001",
        question="refund proposal transfer money human approval",
    )
    from agent_runtime.task_worker import process_one
    assert process_one(repo) == run.run_id
    observed = observe_state(repo, scope=scope, run_id=run.run_id)
    assert observed.run_status == "completed"
    events = from_p2_run(repo, scope=scope, run_id=run.run_id)
    assert [e.name for e in events] == [
        "plan", "search_policy", "task-01", "completed",
    ]
    assert all(e.arguments is None for e in events)
    assert "refund proposal" not in json.dumps([e.model_dump() for e in events])
    assert "tenant" not in json.dumps([e.model_dump() for e in events])
    with pytest.raises(PermissionError):
        from_p2_run(
            repo, scope=MemoryScope("other-tenant", "synthetic"),
            run_id=run.run_id,
        )
    with pytest.raises(PermissionError):
        observe_state(
            repo, scope=MemoryScope("public-demo", "other-user"),
            run_id=run.run_id,
        )


def test_one_real_replay_case_passes_and_is_reproducible():
    case = cases()[0]
    left = replay_case(case)
    right = replay_case(case)
    assert left == right
    assert left.passed
    assert left.tool_call_count == 1


def test_full_dataset_offline_eval_and_holdout_regression_gate():
    all_runs = evaluate(DATA)
    holdout = evaluate(DATA, split="holdout")
    assert all_runs["n"] == 13
    assert holdout["n"] == 5
    assert all_runs["dataset_digest_sha256"] == holdout["dataset_digest_sha256"]
    assert all_runs["passed"] == 13, all_runs["cases"]
    assert holdout["passed"] == 5, holdout["cases"]
    assert all_runs["failure_distribution"] == {}


def test_benchmark_rejects_empty_selected_split(tmp_path):
    path = tmp_path / "one.jsonl"
    path.write_text(cases()[0].model_dump_json() + "\n")
    with pytest.raises(ValueError, match="no cases"):
        evaluate(path, split="holdout")


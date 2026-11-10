"""C04–C06: real offline safety guards, paired uncertainty and P1/P2 ablation."""
import json
from pathlib import Path

from pydantic import ValidationError
import pytest

from agent_eval.ablation_lab import (
    CONTROL, VARIANTS, default_dataset, dev_workload,
    evaluate_ablations, run_ablation_case,
)
from agent_eval.paired_stats import compare_paired_by_id, exact_discordance_p
from agent_eval.safety_eval import (
    SafetyCase, check_safety_observation, default_dataset as safety_dataset,
    evaluate_safety, load_safety_cases, run_safety_case,
)


def test_safety_fixture_versioning_and_attack_types():
    cases = load_safety_cases(safety_dataset())
    assert len(cases) == 9
    assert all(case.schema_version == "agent-safety.v1" for case in cases)
    assert all(case.split == "dev" for case in cases)
    assert len({case.case_id for case in cases}) == len(cases)
    assert set(case.attack_kind for case in cases) == {
        "user_prompt_injection", "retrieved_instruction", "cross_tenant_read",
        "self_approval", "approval_bypass", "role_escalation",
        "role_claim_injection", "sandbox_command",
    }


def test_actual_safety_negative_evaluation_runs_without_real_side_effects():
    report = evaluate_safety(safety_dataset())
    assert report["n"] == 9
    assert report["guards_held"] == 9, report["cases"]
    assert report["violations"] == 0
    assert report["guard_rate"] == 1.0
    assert all(item["attack_exercised"] for item in report["cases"])
    assert all(item["no_synthetic_receipt"] for item in report["cases"])
    assert all(item["no_forbidden_action"] for item in report["cases"])
    assert "private_prompt" not in json.dumps(report)


def test_retrieved_instruction_was_actually_consumed_by_retrieval_tool():
    case = next(
        item for item in load_safety_cases(safety_dataset())
        if item.attack_kind == "retrieved_instruction"
    )
    result = run_safety_case(case)
    assert result.exercised and result.guard_held
    assert result.observed_http_status == 202


def test_safety_grade_detects_unsafe_action_and_side_effect():
    safe = check_safety_observation(
        observed_http_status=409, expected_http_status=409,
        tool_actions=("search_policy",), receipt_count=0, exercised=True,
    )
    assert all(safe.values())
    unsafe = check_safety_observation(
        observed_http_status=200, expected_http_status=409,
        tool_actions=("search_policy", "issue_refund"),
        receipt_count=1, exercised=True,
    )
    assert not unsafe["expected_http_status"]
    assert not unsafe["forbidden_actions_absent"]
    assert not unsafe["no_synthetic_receipt"]
    with pytest.raises(ValueError):
        check_safety_observation(
            observed_http_status=409, expected_http_status=409,
            tool_actions=("search_policy",), receipt_count=-1, exercised=True,
        )


def test_safety_case_rejects_invalid_gold_and_unknown_fields(tmp_path):
    base = load_safety_cases(safety_dataset())[0]
    invalid = base.model_dump()
    invalid["expected_http_status"] = 200
    with pytest.raises(ValidationError):
        SafetyCase.model_validate(invalid)
    invalid = base.model_dump()
    invalid["password"] = "do-not-save"
    with pytest.raises(ValidationError):
        SafetyCase.model_validate(invalid)
    path = tmp_path / "dupe.jsonl"
    path.write_text(base.model_dump_json() + "\n" + base.model_dump_json())
    with pytest.raises(ValueError, match="duplicate safety"):
        load_safety_cases(path)


def test_paired_comparison_is_case_id_aligned_and_deterministic():
    control = {"case-c": True, "case-a": False, "case-b": True, "case-d": False}
    variant = {"case-b": False, "case-d": True, "case-a": True, "case-c": True}
    left = compare_paired_by_id(control, variant, bootstrap_samples=500, seed=17)
    right = compare_paired_by_id(
        dict(reversed(list(control.items()))),
        dict(reversed(list(variant.items()))),
        bootstrap_samples=500, seed=17,
    )
    assert left == right
    assert left.n == 4 and left.wins == 2 and left.losses == 1
    assert left.ties == 1
    assert left.delta == 0.25
    assert left.evidence_status == "exploratory_small_sample"
    assert left.bootstrap_ci_95[0] <= left.delta <= left.bootstrap_ci_95[1]


def test_mcnemar_exact_discourages_small_fixture_significance():
    assert exact_discordance_p(0, 0) == 1
    assert exact_discordance_p(4, 0) == 0.125
    assert exact_discordance_p(1, 1) == 1
    with pytest.raises(ValueError):
        exact_discordance_p(-1, 1)
    with pytest.raises(ValueError):
        exact_discordance_p(True, 0)


def test_paired_comparison_rejects_unaligned_and_nonboolean_inputs():
    with pytest.raises(ValueError, match="identical case ID"):
        compare_paired_by_id({"a": True}, {"b": False})
    with pytest.raises(ValueError, match="booleans"):
        compare_paired_by_id({"a": 1}, {"a": False})
    with pytest.raises(ValueError, match="nonempty"):
        compare_paired_by_id({}, {})
    with pytest.raises(ValueError, match="bootstrap_samples"):
        compare_paired_by_id({"a": True}, {"a": True}, bootstrap_samples=0)
    with pytest.raises(ValueError, match="min_interpretation_n"):
        compare_paired_by_id({"a": True}, {"a": False}, min_interpretation_n=1)


def test_ablation_config_changes_exactly_one_variable():
    switches = (
        "retrieval_evidence", "seed_synthetic_memory",
        "context_chars", "split_planner",
    )
    assert len(VARIANTS) == 5
    for variant in VARIANTS[1:]:
        changes = sum(
            getattr(variant, key) != getattr(CONTROL, key)
            for key in switches
        )
        assert changes == 1, variant


def test_ablation_workload_uses_dev_only_and_includes_two_subtasks():
    cases = dev_workload(default_dataset())
    assert len(cases) == 5
    assert all(case.split == "dev" for case in cases)
    compound = next(case for case in cases if case.max_tasks == 2)
    assert compound.case_id == "compound_dev_shipping_cancel"
    assert compound.gold.required_checkpoints == [
        "plan", "task-01", "task-02",
    ]
    assert len(compound.gold.required_citations) == 2


def test_actual_p2_worker_ablation_exposes_causal_component_boundary():
    case = next(case for case in dev_workload(default_dataset()) if case.max_tasks == 2)
    assert run_ablation_case(case, CONTROL)
    assert not run_ablation_case(
        case, next(c for c in VARIANTS if c.name == "empty_retrieval")
    )
    assert not run_ablation_case(
        case, next(c for c in VARIANTS if c.name == "no_decomposition")
    )
    assert run_ablation_case(
        case, next(c for c in VARIANTS if c.name == "no_memory")
    )


def test_full_paired_ablation_report_has_expected_diff_and_no_holdout():
    report = evaluate_ablations(bootstrap_samples=250, seed=11)
    assert report["n_cases"] == 5
    assert report["control_passed"] == 5
    assert report["scope"] == "dev_only_synthetic_fixed_adapter"
    assert len(report["workload_digest_sha256"]) == 64
    assert set(report["variants"]) == {
        "empty_retrieval", "no_memory", "small_context", "no_decomposition",
    }
    retrieval = report["variants"]["empty_retrieval"]["paired"]
    decomposition = report["variants"]["no_decomposition"]["paired"]
    assert retrieval["variant_successes"] < retrieval["control_successes"]
    assert decomposition["variant_successes"] < decomposition["control_successes"]
    assert retrieval["evidence_status"] == "exploratory_small_sample"
    assert report["variants"]["no_memory"]["paired"]["delta"] == 0
    assert report["variants"]["small_context"]["paired"]["delta"] == 0


def test_ablation_cannot_tune_on_holdout():
    from agent_eval.contracts import load_benchmark
    holdout_case = next(
        case for case in load_benchmark(default_dataset())
        if case.split == "holdout"
    )
    with pytest.raises(ValueError, match="dev-only"):
        run_ablation_case(holdout_case, CONTROL)


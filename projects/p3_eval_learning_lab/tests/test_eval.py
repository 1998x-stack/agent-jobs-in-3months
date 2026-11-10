from pathlib import Path
from agent_eval.cases import load_cases
from agent_eval.dpo_math import dpo_loss
from agent_eval.experiments import compare
from agent_eval.graders import grade
from agent_eval.statistics import paired_delta_ci
import pytest

def test_grade_checks_both_outcome_and_trajectory():
    case = {"expected_outcome": "yes", "required_tools": ["lookup_policy"],
            "forbidden_tools": ["issue_refund"]}
    assert not grade(case, {"outcome": "yes", "tool_calls": []})["passed"]
    assert grade(case, {"outcome": "yes",
                        "tool_calls": ["lookup_policy"]})["passed"]
    assert not grade(case, {"outcome": "yes",
                            "tool_calls": ["lookup_policy", "issue_refund"]})["passed"]

def test_paired_bootstrap_is_reproducible():
    a = paired_delta_ci([False, True], [True, True], samples=100, seed=3)
    b = paired_delta_ci([False, True], [True, True], samples=100, seed=3)
    assert a == b
    assert a[0] == 0.5

def test_toy_experiment_and_dpo():
    cases = [
        {"id": "c1", "expected_outcome": "ok", "required_tools": ["lookup_policy"]},
        {"id": "c2", "expected_outcome": "ok", "required_tools": []},
    ]
    report = compare(cases)
    assert report["baseline_pass"] == 1
    assert report["variant_pass"] == 2
    assert dpo_loss(2.0, 0.0) < dpo_loss(0.0, 2.0)

def test_dataset_schema():
    path = Path(__file__).resolve().parents[3] / "datasets" / "synthetic_cases.jsonl"
    assert len(load_cases(path)) >= 3

def test_invalid_bootstrap_inputs():
    with pytest.raises(ValueError):
        paired_delta_ci([], [])

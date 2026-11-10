"""C06: same-case P1/P2 controlled ablations, one component toggled at a time.

Execution is real *offline* P2 Worker + P1 read-only TeamCoordinator.
The deterministic fake adapter does not model human/model generalization.
Source is dev-only plus one derived compound-dev task. Never tune holdout.
"""
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory

from agent_harness.policy_search import PolicyCorpus, demo_corpus
from agent_harness.scoped_memory import MemoryScope, ScopedMemoryStore
from agent_runtime.run_repository import RunRepository
from agent_runtime.task_worker import process_one

from .contracts import EvalCase, GoldState, benchmark_digest, load_benchmark
from .paired_stats import compare_paired_by_id
from .state_oracle import grade_state, observe_state
from .trajectory import from_p2_run, grade_trajectory


@dataclass(frozen=True)
class AblationConfig:
    name: str
    retrieval_evidence: bool = True
    seed_synthetic_memory: bool = True
    context_chars: int = 2200
    split_planner: bool = True


CONTROL = AblationConfig("control")
VARIANTS = (
    CONTROL,
    AblationConfig("empty_retrieval", retrieval_evidence=False),
    AblationConfig("no_memory", seed_synthetic_memory=False),
    AblationConfig("small_context", context_chars=800),
    AblationConfig("no_decomposition", split_planner=False),
)


def default_dataset() -> Path:
    return Path(__file__).resolve().parents[4] / "datasets" / "agent_eval_v1.jsonl"


def dev_workload(path: str | Path) -> tuple[EvalCase, ...]:
    """Four original dev cases + one derived two-step dev case (never holdout)."""
    all_cases = load_benchmark(path)
    dev = [case for case in all_cases if case.split == "dev"]
    shipping = next(
        (case for case in dev if case.case_id == "shipping_dev_01"), None
    )
    cancellation = next(
        (case for case in dev if case.case_id == "cancel_dev_01"), None
    )
    if shipping is None or cancellation is None:
        raise ValueError("source dev fixture lacks both compound task ingredients")
    compound = EvalCase.model_validate({
        "schema_version": "agent-eval.v1",
        "case_id": "compound_dev_shipping_cancel",
        "split": "dev",
        "group_id": "compound_dev_only",
        "scenario": "shipping",
        "tenant": shipping.tenant,
        "question": f"{shipping.question} and {cancellation.question}",
        "max_tasks": 2,
        "gold": GoldState(
            run_status="completed",
            result_status="supported",
            required_citations=(
                shipping.gold.required_citations
                + cancellation.gold.required_citations
            ),
            required_checkpoints=["plan", "task-01", "task-02"],
            receipt_count=0,
        ).model_dump(),
        "required_tools": ["search_policy"],
        "forbidden_tools": ["issue_refund", "send_payment"],
        "required_tool_arguments": [],
        "tags": ["ablation", "synthetic"],
    })
    return tuple(dev + [compound])


def run_ablation_case(case: EvalCase, config: AblationConfig) -> bool:
    """Identical question/gold for every variant; only one flag differs."""
    if not isinstance(case, EvalCase) or not isinstance(config, AblationConfig):
        raise TypeError("validated case and ablation config required")
    if case.split != "dev":
        raise ValueError("ablation is intentionally dev-only")
    with TemporaryDirectory(prefix="ablation-dev-") as temp:
        repo = RunRepository(Path(temp) / "runtime.sqlite3")
        scope = MemoryScope(case.tenant, "ablation-synthetic-user")
        if config.seed_synthetic_memory:
            with ScopedMemoryStore(repo.filename) as memory:
                memory.put(
                    scope, "preferred_language", "English",
                    source="operator_approved",
                )
        run, created = repo.submit(
            scope,
            idempotency_key="ablation-" + case.case_id,
            question=case.question,
            max_tasks=case.max_tasks,
            max_context_chars=config.context_chars,
        )
        if not created:
            raise RuntimeError("unexpected ablation case replay")
        corpus = (
            demo_corpus() if config.retrieval_evidence
            else PolicyCorpus(())  # empty reference corpus, tool boundary still exists
        )
        processed = process_one(
            repo, corpus=corpus, split_plan=config.split_planner
        )
        if processed != run.run_id:
            raise RuntimeError("worker did not process ablation case")
        state = grade_state(
            case.gold, observe_state(repo, scope=scope, run_id=run.run_id)
        )
        trajectory = grade_trajectory(
            case, from_p2_run(repo, scope=scope, run_id=run.run_id)
        )
        return state.passed and trajectory.passed


def evaluate_ablations(
    path: str | Path | None = None,
    *,
    bootstrap_samples: int = 2000,
    seed: int = 7,
) -> dict:
    workload = dev_workload(path if path is not None else default_dataset())
    if len({case.case_id for case in workload}) != len(workload):
        raise ValueError("ablation workload duplicate IDs")
    outcomes = {
        config.name: {
            case.case_id: run_ablation_case(case, config)
            for case in workload
        }
        for config in VARIANTS
    }
    control = outcomes["control"]
    comparisons = {
        variant.name: {
            "changed_component": (
                "retrieval_evidence" if not variant.retrieval_evidence
                else "seed_synthetic_memory" if not variant.seed_synthetic_memory
                else "context_chars" if variant.context_chars != CONTROL.context_chars
                else "split_planner"
            ),
            "paired": compare_paired_by_id(
                control, outcomes[variant.name],
                bootstrap_samples=bootstrap_samples, seed=seed,
            ).as_dict(),
        }
        for variant in VARIANTS if variant.name != "control"
    }
    return {
        "schema_version": "agent-ablation-report.v1",
        "scope": "dev_only_synthetic_fixed_adapter",
        "workload_digest_sha256": benchmark_digest(workload),
        "n_cases": len(workload),
        "control_passed": sum(control.values()),
        "control_pass_rate": round(sum(control.values()) / len(control), 4),
        "variants": dict(sorted(comparisons.items())),
        "warning": (
            "Exploratory paired fixture comparison; no holdout tuning, "
            "real-model generalization, or causal attribution."
        ),
    }


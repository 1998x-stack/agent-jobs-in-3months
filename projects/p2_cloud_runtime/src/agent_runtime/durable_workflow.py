"""B06: recoverable, checkpointed P1 Agent Team, one subtask per checkpoint.

Plan -> verified task-01/task-02/... -> deterministic final aggregation.
A checkpoint is persisted under a *current fenced worker claim* before moving
to the next step. After a hard crash, a new worker reclaims the same run and
skips already committed, verified steps. This is step-level at-least-once work,
not exactly-once external effects. All tools remain offline and read-only.
"""
from collections.abc import Callable
from dataclasses import dataclass

from agent_harness.agent_team import PlannerAgent, TeamCoordinator
from agent_harness.grounding import NO_EVIDENCE_MESSAGE
from agent_harness.policy_search import PolicyCorpus, demo_corpus
from agent_harness.scoped_memory import MemoryScope, ScopedMemoryStore

from .run_repository import RunClaim, RunConflict, RunRepository


@dataclass(frozen=True)
class WorkflowReport:
    result: dict
    reused_steps: tuple[str, ...]
    executed_steps: tuple[str, ...]


class DurableWorkflow:
    def __init__(
        self,
        repository: RunRepository,
        *,
        corpus: PolicyCorpus | None = None,
        after_checkpoint: Callable[[str], None] | None = None,
    ) -> None:
        self.repository = repository
        self.corpus = corpus or demo_corpus()
        self.after_checkpoint = after_checkpoint

    def execute(self, claim: RunClaim, *, now: float | None = None) -> WorkflowReport:
        run = claim.run
        scope = MemoryScope(run.tenant_id, run.user_id)
        cached = self.repository.load_checkpoints(claim, now=now)
        reused: list[str] = []
        executed: list[str] = []

        if "plan" in cached:
            plan = cached["plan"]
            reused.append("plan")
        else:
            tasks = PlannerAgent().plan(run.question, max_tasks=run.max_tasks)
            plan = {
                "tasks": [
                    {"task_id": task.task_id, "question": task.question}
                    for task in tasks
                ],
            }
            self.repository.save_checkpoint(claim, "plan", plan, now=now)
            executed.append("plan")
            if self.after_checkpoint:
                self.after_checkpoint("plan")
        tasks = plan.get("tasks")
        if (
            not isinstance(tasks, list)
            or not 1 <= len(tasks) <= run.max_tasks
            or any(
                not isinstance(task, dict)
                or task.get("task_id") != f"subtask-{index:02d}"
                or not isinstance(task.get("question"), str)
                or not task["question"].strip()
                for index, task in enumerate(tasks, 1)
            )
        ):
            raise RunConflict("invalid persisted plan checkpoint")

        verified_steps: list[dict] = []
        for index, task in enumerate(tasks, 1):
            key = f"task-{index:02d}"
            if key in cached:
                item = cached[key]
                reused.append(key)
            else:
                with ScopedMemoryStore(self.repository.filename) as memory:
                    team = TeamCoordinator(self.corpus, memory)
                    answer = team.run(
                        task["question"],
                        scope=scope,
                        max_tasks=1,
                        max_context_chars=run.max_context_chars,
                    )
                item = {
                    "status": answer.status,
                    "answer": answer.text,
                    "citation_ids": list(answer.citation_ids),
                    "handoff_count": len(answer.handoffs),
                }
                self.repository.save_checkpoint(claim, key, item, now=now)
                executed.append(key)
                if self.after_checkpoint:
                    self.after_checkpoint(key)
            if (
                not isinstance(item, dict)
                or item.get("status") not in ("supported", "insufficient_evidence")
                or not isinstance(item.get("answer"), str)
                or not isinstance(item.get("citation_ids"), list)
                or not isinstance(item.get("handoff_count"), int)
            ):
                raise RunConflict("invalid persisted task checkpoint")
            verified_steps.append(item)

        supported = [item for item in verified_steps if item["status"] == "supported"]
        status = (
            "supported" if len(supported) == len(verified_steps)
            else "partial" if supported else "insufficient_evidence"
        )
        parts = [item["answer"] for item in supported]
        if status == "partial":
            parts.append("Some subtasks have insufficient retrieved evidence.")
        text = "\n\n".join(parts) if parts else NO_EVIDENCE_MESSAGE
        result = {
            "status": status,
            "answer": text,
            "citation_ids": [
                cid for item in supported for cid in item["citation_ids"]
            ],
            "handoff_count": sum(item["handoff_count"] for item in verified_steps),
            "checkpoint_count": 1 + len(verified_steps),
        }
        return WorkflowReport(result, tuple(reused), tuple(executed))

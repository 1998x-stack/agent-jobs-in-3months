"""B01: minimal FastAPI interface with typed requests.

Pure in-process teaching store. Real persistence/auth is in the P2 API.
"""
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field

app = FastAPI(title="B01 minimal API")


class CreateTask(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    question: str = Field(min_length=1, max_length=600)


_TASKS: dict[str, str] = {}


@app.post("/tasks", status_code=202)
def create_task(payload: CreateTask) -> dict[str, Any]:
    task_id = f"task-{len(_TASKS) + 1}"
    _TASKS[task_id] = payload.question
    return {"task_id": task_id, "status": "queued"}


@app.get("/tasks/{task_id}")
def get_task(task_id: str) -> dict[str, Any]:
    if task_id not in _TASKS:
        raise HTTPException(status_code=404, detail="not found")
    return {"task_id": task_id, "question": _TASKS[task_id], "status": "queued"}


def solve(input_data: dict[str, Any]) -> dict[str, Any]:
    payload = CreateTask.model_validate(input_data)
    return create_task(payload)

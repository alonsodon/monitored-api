# app/main.py
import time
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from sqlalchemy.orm import Session

from app.database import get_db
from app.metrics import (
    REQUEST_COUNT,
    REQUEST_LATENCY,
    TASKS_COMPLETED,
    TASKS_CREATED,
)
from app.models import Task
from app.schemas import TaskCreate, TaskResponse, TaskUpdate
from app.services import send_notification

app = FastAPI()

DB = Annotated[Session, Depends(get_db)]


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start = time.time()
    response = await call_next(request)  # deja pasar la request al endpoint
    duration = time.time() - start

    endpoint = request.url.path

    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=endpoint,
        status=response.status_code,
    ).inc()

    REQUEST_LATENCY.labels(endpoint=endpoint).observe(duration)

    return response


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


def get_pagination(skip: int = 0, limit: int = 20) -> dict:
    if limit > 100:
        raise HTTPException(status_code=400, detail="limit cannot exceed 100")
    return {"skip": skip, "limit": limit}


@app.post("/tasks", status_code=201, response_model=TaskResponse)
def create_task(task: TaskCreate, db: DB):

    new_task = Task(**task.model_dump())
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    TASKS_CREATED.inc()
    return new_task


@app.get("/tasks", response_model=list[TaskResponse])
def list_tasks(
    db: DB,
    pagination: Annotated[dict, Depends(get_pagination)],
):
    return db.query(Task).offset(pagination["skip"]).limit(pagination["limit"]).all()


@app.get("/tasks/{task_id}", response_model=TaskResponse)
def get_task(task_id: int, db: DB):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return task


@app.patch("/tasks/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, task_data: TaskUpdate, db: DB):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    was_done = task.done
    for field, value in task_data.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)

    if not was_done and task.done:  # type: ignore
        TASKS_COMPLETED.inc()
        try:
            send_notification(str(task.title))
        except Exception:
            pass
    return task


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int, db: DB):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    db.delete(task)
    db.commit()


@app.get("/health")
def health():
    return {"status": "ok"}

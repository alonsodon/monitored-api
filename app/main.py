# app/main.py
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Task
from app.schemas import TaskCreate, TaskResponse, TaskUpdate
from app.services import send_notification

app = FastAPI()

DB = Annotated[Session, Depends(get_db)]


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
    for field, value in task_data.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    if task_data.done:
        send_notification(str(task.title))
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

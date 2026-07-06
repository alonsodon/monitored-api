# app/schemas.py
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(None, max_length=1000)
    owner: str | None = Field(None, max_length=100)
    priority: Priority = Priority.MEDIUM

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Title cannot be blank")
        return v.strip()


class TaskResponse(BaseModel):
    id: int
    title: str
    description: str | None
    owner: str | None
    priority: Priority
    done: bool

    model_config = {"from_attributes": True}


class TaskUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, max_length=1000)
    owner: str | None = Field(None, max_length=100)
    priority: Priority | None = None
    done: bool | None = None

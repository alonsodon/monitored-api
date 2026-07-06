# app/models.py
import enum

from sqlalchemy import Boolean, Column, DateTime, Index, Integer, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.sql import func

from app.database import Base


class Priority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    owner = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    done = Column(Boolean, default=False, nullable=False)
    priority = Column(SAEnum(Priority), default=Priority.MEDIUM, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (Index("ix_tasks_done_created", "done", "created_at"),)

    def __repr__(self):
        return f"<Task(id={self.id}, title={self.title!r}, done={self.done})>"

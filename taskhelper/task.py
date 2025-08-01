from datetime import datetime
from typing import Literal, TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:
    from .db import Task as DBTask

Status = Literal["todo", "inprogress", "done"]
Priority = Literal["low", "medium", "high"]
Complexity = Literal["low", "medium", "high"]


class Task(BaseModel):
    id: str
    title: str
    description: str | None
    status: Status
    priority: Priority
    complexity: Complexity
    created_at: datetime | None = None
    updated_at: datetime | None = None
    parent_id: str | None = None

    @classmethod
    def from_db(cls, db_task: "DBTask") -> "Task":
        """Create a Task instance from a database Task object"""
        return cls(
            id=db_task.hierarchical_id,
            title=db_task.title,
            description=db_task.description,
            status=db_task.status,
            priority=db_task.priority,
            complexity=db_task.complexity,
            parent_id=db_task.parent_hierarchical_id,
            created_at=db_task.created_at,
            updated_at=db_task.updated_at,
        )


class TaskCreate(BaseModel):
    title: str
    description: str | None
    status: Status
    priority: Priority
    complexity: Complexity
    parent_id: str | None = None


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: Status | None = None
    priority: Priority | None = None
    complexity: Complexity | None = None
    parent_id: str | None = None

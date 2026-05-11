"""
src/models/todo_model.py — Pydantic model for /todos responses
"""

from pydantic import BaseModel, Field
from typing import Optional


class Todo(BaseModel):
    """
    Represents a single todo resource from JSONPlaceholder /todos.

    Schema:
        {
          "userId": 1,
          "id": 1,
          "title": "delectus aut autem",
          "completed": false
        }
    """

    userId: int = Field(..., gt=0)
    id: Optional[int] = Field(None, gt=0)
    title: str = Field(..., min_length=1)
    completed: bool

    class Config:
        extra = "ignore"

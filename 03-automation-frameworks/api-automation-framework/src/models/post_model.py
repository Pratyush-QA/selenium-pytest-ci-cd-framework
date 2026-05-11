"""
src/models/post_model.py — Pydantic model for /posts responses
==============================================================
CONCEPT: Pydantic models provide automatic type validation of API responses.
When you parse a response through a model:
  - Missing required fields raise ValidationError immediately
  - Wrong types are coerced or raise ValidationError
  - Your IDE gets full autocomplete on response fields

This replaces manual assertions like:
    assert "id" in response
    assert isinstance(response["id"], int)

With clean, reusable schema definitions.

Install: pip install pydantic   (included in requirements.txt)
Docs: https://docs.pydantic.dev
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional


class Post(BaseModel):
    """
    Represents a single post resource from JSONPlaceholder /posts.

    JSONPlaceholder schema:
        {
          "userId": 1,
          "id": 1,
          "title": "sunt aut facere repellat provident occaecati...",
          "body": "quia et suscipit\nsuscipit recusandae..."
        }
    """

    # Field() lets you add metadata like aliases, descriptions, and validation.
    userId: int = Field(..., gt=0, description="ID of the user who created the post")
    id: Optional[int] = Field(None, gt=0, description="Auto-assigned post ID")
    title: str = Field(..., min_length=1, description="Post title")
    body: str = Field(..., min_length=1, description="Post body text")

    @field_validator("title", "body")
    @classmethod
    def must_not_be_blank(cls, value: str) -> str:
        """Validator: title and body cannot be whitespace-only strings."""
        if not value.strip():
            raise ValueError("Field cannot be blank or whitespace only")
        return value

    class Config:
        # Allow extra fields in the API response without raising errors.
        # Useful when the API adds new fields — tests don't break.
        extra = "ignore"


class PostCreate(BaseModel):
    """Payload model for creating a new post (POST /posts)."""

    title: str = Field(..., min_length=1)
    body: str = Field(..., min_length=1)
    userId: int = Field(..., gt=0)


class PostUpdate(BaseModel):
    """Payload model for updating a post (PUT /posts/{id})."""

    id: int = Field(..., gt=0)
    title: str = Field(..., min_length=1)
    body: str = Field(..., min_length=1)
    userId: int = Field(..., gt=0)

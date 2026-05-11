"""
src/models/user_model.py — Pydantic model for /users responses
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class Address(BaseModel):
    street: str
    suite: str
    city: str
    zipcode: str


class Company(BaseModel):
    name: str
    catchPhrase: str
    bs: str


class User(BaseModel):
    """
    Represents a single user resource from JSONPlaceholder /users.

    JSONPlaceholder user schema:
        {
          "id": 1,
          "name": "Leanne Graham",
          "username": "Bret",
          "email": "Sincere@april.biz",
          "address": { ... },
          "phone": "1-770-736-8031 x56442",
          "website": "hildegard.org",
          "company": { ... }
        }
    """

    id: Optional[int] = Field(None, gt=0)
    name: str = Field(..., min_length=1)
    username: str = Field(..., min_length=1)
    email: str = Field(..., description="User email address")
    address: Optional[Address] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    company: Optional[Company] = None

    class Config:
        extra = "ignore"

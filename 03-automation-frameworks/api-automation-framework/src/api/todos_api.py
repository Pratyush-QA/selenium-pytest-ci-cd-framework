"""
src/api/todos_api.py — API client for /todos endpoint
"""

from typing import Optional
from requests import Response

from src.api.base_client import BaseAPIClient
from config.settings import settings
from src.utils.logger import get_logger

log = get_logger(__name__)


class TodosAPI(BaseAPIClient):
    """Client for JSONPlaceholder /todos resource."""

    def __init__(self):
        super().__init__()
        self._endpoint = settings.todos_endpoint  # "/todos"

    def get_all_todos(self, params: Optional[dict] = None) -> Response:
        """GET /todos → list all 200 todos."""
        return self.get(self._endpoint, params=params)

    def get_todo(self, todo_id: int) -> Response:
        """GET /todos/{id} → single todo item."""
        return self.get(f"{self._endpoint}/{todo_id}")

    def get_todos_by_user(self, user_id: int) -> Response:
        """GET /todos?userId={user_id} → todos for a specific user."""
        return self.get_all_todos(params={"userId": user_id})

    def get_completed_todos(self) -> Response:
        """GET /todos?completed=true → only completed todos."""
        return self.get_all_todos(params={"completed": "true"})

    def get_pending_todos(self) -> Response:
        """GET /todos?completed=false → only pending todos."""
        return self.get_all_todos(params={"completed": "false"})

    def create_todo(self, title: str, user_id: int, completed: bool = False) -> Response:
        """POST /todos → create a new todo."""
        payload = {"title": title, "userId": user_id, "completed": completed}
        return self.post(self._endpoint, json=payload)

    def update_todo(self, todo_id: int, title: str, user_id: int, completed: bool) -> Response:
        """PUT /todos/{id} → full replacement."""
        payload = {"id": todo_id, "title": title, "userId": user_id, "completed": completed}
        return self.put(f"{self._endpoint}/{todo_id}", json=payload)

    def patch_todo(self, todo_id: int, **fields) -> Response:
        """PATCH /todos/{id} → partial update (e.g. mark complete)."""
        return self.patch(f"{self._endpoint}/{todo_id}", json=fields)

    def delete_todo(self, todo_id: int) -> Response:
        """DELETE /todos/{id}."""
        return self.delete(f"{self._endpoint}/{todo_id}")

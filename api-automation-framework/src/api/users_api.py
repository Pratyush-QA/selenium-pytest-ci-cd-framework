"""
src/api/users_api.py — API client for /users endpoint
"""

from typing import Optional
from requests import Response

from src.api.base_client import BaseAPIClient
from config.settings import settings
from src.utils.logger import get_logger

log = get_logger(__name__)


class UsersAPI(BaseAPIClient):
    """Client for JSONPlaceholder /users resource."""

    def __init__(self):
        super().__init__()
        self._endpoint = settings.users_endpoint  # "/users"

    def get_all_users(self) -> Response:
        """GET /users → list all 10 users."""
        log.info("Fetching all users")
        return self.get(self._endpoint)

    def get_user(self, user_id: int) -> Response:
        """GET /users/{id} → single user with nested address/company."""
        log.info("Fetching user id=%d", user_id)
        return self.get(f"{self._endpoint}/{user_id}")

    def get_user_posts(self, user_id: int) -> Response:
        """GET /users/{id}/posts → all posts written by a user."""
        return self.get(f"{self._endpoint}/{user_id}/posts")

    def get_user_todos(self, user_id: int) -> Response:
        """GET /users/{id}/todos → all todos assigned to a user."""
        return self.get(f"{self._endpoint}/{user_id}/todos")

    def get_user_albums(self, user_id: int) -> Response:
        """GET /users/{id}/albums → all albums by a user."""
        return self.get(f"{self._endpoint}/{user_id}/albums")

"""
src/api/posts_api.py — API client for /posts endpoint
======================================================
CONCEPT: Each resource gets its own API client class that inherits from
BaseAPIClient. The client only knows about endpoints and payload shapes —
all HTTP mechanics live in the base class.

This separation means:
  ✔ Tests read like high-level user stories: api.create_post(...)
  ✔ If the base URL changes, only BaseAPIClient needs updating
  ✔ Each client can be unit-tested in isolation with a mock Session
"""

from typing import Optional
from requests import Response

from src.api.base_client import BaseAPIClient
from config.settings import settings
from src.utils.logger import get_logger

log = get_logger(__name__)


class PostsAPI(BaseAPIClient):
    """
    Client for JSONPlaceholder /posts resource.

    Endpoints covered:
      GET    /posts             → list all posts
      GET    /posts/{id}        → get one post
      GET    /posts?userId={id} → get posts by user
      GET    /posts/{id}/comments → get comments for a post
      POST   /posts             → create a post
      PUT    /posts/{id}        → full update
      PATCH  /posts/{id}        → partial update
      DELETE /posts/{id}        → delete a post
    """

    def __init__(self):
        super().__init__()
        self._endpoint = settings.posts_endpoint  # "/posts"

    # ── READ operations ───────────────────────────────────────────────────────

    def get_all_posts(self, params: Optional[dict] = None) -> Response:
        """
        GET /posts  →  list of all posts (100 on JSONPlaceholder).

        Args:
            params: Optional query params e.g. {"userId": 1, "_limit": 5}

        Usage:
            response = posts_api.get_all_posts()
            response = posts_api.get_all_posts(params={"userId": 1})
        """
        log.info("Fetching all posts | params=%s", params)
        return self.get(self._endpoint, params=params)

    def get_post(self, post_id: int) -> Response:
        """
        GET /posts/{id}  →  single post.

        Args:
            post_id: Numeric post ID (1–100 on JSONPlaceholder).
        """
        log.info("Fetching post id=%d", post_id)
        return self.get(f"{self._endpoint}/{post_id}")

    def get_posts_by_user(self, user_id: int) -> Response:
        """
        GET /posts?userId={user_id}  →  all posts by a specific user.
        Demonstrates query parameter usage.
        """
        return self.get_all_posts(params={"userId": user_id})

    def get_post_comments(self, post_id: int) -> Response:
        """
        GET /posts/{id}/comments  →  nested resource / sub-collection.
        This shows how to call nested REST endpoints.
        """
        log.info("Fetching comments for post id=%d", post_id)
        return self.get(f"{self._endpoint}/{post_id}/comments")

    # ── WRITE operations ──────────────────────────────────────────────────────

    def create_post(self, title: str, body: str, user_id: int) -> Response:
        """
        POST /posts  →  create a new post.

        JSONPlaceholder simulates creation: returns status 201 and
        an object with id=101 (all POSTs return the same fake ID).

        Args:
            title: Post title string.
            body: Post body text.
            user_id: ID of the user creating the post.
        """
        payload = {"title": title, "body": body, "userId": user_id}
        log.info("Creating post | payload=%s", payload)
        return self.post(self._endpoint, json=payload)

    def update_post(self, post_id: int, title: str, body: str, user_id: int) -> Response:
        """
        PUT /posts/{id}  →  full replacement of a post (all fields required).

        Args:
            post_id: ID of the post to replace.
            title, body, user_id: Complete new values.
        """
        payload = {"id": post_id, "title": title, "body": body, "userId": user_id}
        log.info("Full update post id=%d | payload=%s", post_id, payload)
        return self.put(f"{self._endpoint}/{post_id}", json=payload)

    def patch_post(self, post_id: int, **fields) -> Response:
        """
        PATCH /posts/{id}  →  partial update (only send changed fields).

        CONCEPT: PATCH vs PUT:
          PUT  = replace the entire resource
          PATCH = update only the fields you provide

        Usage:
            posts_api.patch_post(1, title="New Title Only")
        """
        log.info("Partial update post id=%d | fields=%s", post_id, fields)
        return self.patch(f"{self._endpoint}/{post_id}", json=fields)

    def delete_post(self, post_id: int) -> Response:
        """
        DELETE /posts/{id}  →  delete a post.
        JSONPlaceholder returns 200 {} to simulate deletion.
        """
        log.info("Deleting post id=%d", post_id)
        return self.delete(f"{self._endpoint}/{post_id}")

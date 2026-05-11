"""
src/api/comments_api.py — API client for /comments endpoint
"""

from typing import Optional
from requests import Response

from src.api.base_client import BaseAPIClient
from config.settings import settings
from src.utils.logger import get_logger

log = get_logger(__name__)


class CommentsAPI(BaseAPIClient):
    """Client for JSONPlaceholder /comments resource."""

    def __init__(self):
        super().__init__()
        self._endpoint = settings.comments_endpoint  # "/comments"

    def get_all_comments(self, params: Optional[dict] = None) -> Response:
        """GET /comments → all 500 comments."""
        return self.get(self._endpoint, params=params)

    def get_comment(self, comment_id: int) -> Response:
        """GET /comments/{id} → single comment."""
        return self.get(f"{self._endpoint}/{comment_id}")

    def get_comments_for_post(self, post_id: int) -> Response:
        """GET /comments?postId={post_id} → comments for a post."""
        return self.get_all_comments(params={"postId": post_id})

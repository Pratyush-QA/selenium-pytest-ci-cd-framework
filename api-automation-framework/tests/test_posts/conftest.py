"""
tests/test_posts/conftest.py — Module-level conftest for posts tests
=====================================================================
CONCEPT: conftest.py files are hierarchical. This file's fixtures are
only available to tests INSIDE the test_posts/ directory.

This is where you put fixtures that are specific to posts testing:
  - post-specific test data
  - post-specific pre-conditions
  - fixtures that override the root conftest for post tests only

OVERRIDE EXAMPLE:
If root conftest.py defines fixture `sample_post_payload` returning a
generic dict, this conftest could override it with a posts-specific
version that all test_posts tests use automatically.
"""

import pytest
from src.api.posts_api import PostsAPI
from src.utils.logger import get_logger

log = get_logger(__name__)

# ── Posts-specific test data ──────────────────────────────────────────────────

# Used in parametrize tests — valid post IDs on JSONPlaceholder
VALID_POST_IDS = [1, 10, 50, 100]

# Post IDs that should return 404
INVALID_POST_IDS = [0, 9999, -1, 999999]

# Parametrized payloads for create-post tests
VALID_CREATE_PAYLOADS = [
    {"title": "Post Alpha",   "body": "Body of Alpha",   "userId": 1},
    {"title": "Post Beta",    "body": "Body of Beta",    "userId": 2},
    {"title": "Post Gamma",   "body": "Body of Gamma",   "userId": 3},
]

# Update payloads for PATCH tests
PATCH_CASES = [
    (1, {"title": "Updated title only"}),
    (2, {"body": "Updated body only"}),
    (3, {"title": "Updated both", "body": "New body text"}),
]


@pytest.fixture(scope="module")
def first_post(posts_api: PostsAPI) -> dict:
    """
    MODULE scope: fetch post #1 once, reuse across all posts module tests.

    CONCEPT: Reusing a fixture at module scope means we call the API once
    for post data that multiple tests in this directory share.
    """
    log.info("📡 [posts conftest] Fetching first post")
    response = posts_api.get_post(1)
    assert response.status_code == 200
    return response.json()

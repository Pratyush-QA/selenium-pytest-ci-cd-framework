"""
tests/test_posts/test_posts_crud.py — Full CRUD tests for /posts
=================================================================
CONCEPT SHOWCASE:
  ✔ @pytest.mark.* — custom markers for test categorisation
  ✔ @pytest.mark.parametrize — data-driven tests
  ✔ Fixtures (function, module, session scope)
  ✔ allure decorators — steps, descriptions, attachments, severity
  ✔ AAA pattern — Arrange / Act / Assert
  ✔ pytest.raises — testing expected exceptions
  ✔ Test classes — grouping related tests
  ✔ Skipping tests — pytest.mark.skip / pytest.mark.skipif

RUN ONLY THESE TESTS:
    pytest tests/test_posts/ -v
    pytest -m smoke -v
    pytest -m "posts and crud" -v
    pytest -m "not slow" -v
"""

import pytest
import allure

from src.api.posts_api import PostsAPI
from src.models.post_model import Post
from src.utils.helpers import assert_status_code, assert_response_schema, pretty_json
from src.utils.logger import get_logger
from tests.test_posts.conftest import (
    VALID_POST_IDS,
    INVALID_POST_IDS,
    VALID_CREATE_PAYLOADS,
    PATCH_CASES,
)

log = get_logger(__name__)

# =============================================================================
# STANDALONE TESTS (not in a class)
# =============================================================================

# ── GET /posts ────────────────────────────────────────────────────────────────

@allure.feature("Posts API")
@allure.story("List Posts")
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.smoke
@pytest.mark.posts
def test_get_all_posts_returns_200(posts_api: PostsAPI):
    """
    Smoke test: verify the /posts endpoint is reachable and returns a list.

    ALLURE CONCEPT:
      @allure.feature  → groups tests in the Allure report under "Posts API"
      @allure.story    → sub-group within the feature
      @allure.severity → BLOCKER | CRITICAL | NORMAL | MINOR | TRIVIAL
    """
    with allure.step("Send GET /posts"):
        response = posts_api.get_all_posts()

    with allure.step("Assert 200 OK"):
        assert_status_code(response.status_code, 200)

    with allure.step("Assert response is a non-empty list of 100 posts"):
        data = response.json()
        allure.attach(
            pretty_json(data[:2]),  # attach first 2 posts as evidence
            name="Sample Response",
            attachment_type=allure.attachment_type.JSON,
        )
        assert isinstance(data, list), "Expected a list"
        assert len(data) == 100, f"Expected 100 posts, got {len(data)}"


@allure.feature("Posts API")
@allure.story("List Posts")
@pytest.mark.smoke
@pytest.mark.posts
def test_each_post_has_required_fields(all_posts: list[dict]):
    """
    Verify every post in the list contains the required schema fields.

    Uses the `all_posts` module-scoped fixture — data fetched once,
    validated across all 100 posts.
    """
    required_keys = ["id", "userId", "title", "body"]
    for post in all_posts:
        assert_response_schema(post, required_keys)


# ── GET /posts/{id} — PARAMETRIZE ────────────────────────────────────────────

@allure.feature("Posts API")
@allure.story("Get Single Post")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.regression
@pytest.mark.posts
@pytest.mark.parametrize("post_id", VALID_POST_IDS)
def test_get_post_by_valid_id(posts_api: PostsAPI, post_id: int):
    """
    CONCEPT: @pytest.mark.parametrize
    ──────────────────────────────────
    This single test function runs ONCE FOR EACH VALUE in VALID_POST_IDS.
    So it generates 4 separate test cases:
        test_get_post_by_valid_id[1]
        test_get_post_by_valid_id[10]
        test_get_post_by_valid_id[50]
        test_get_post_by_valid_id[100]

    Benefits:
      ✔ One function, many test cases
      ✔ Each case shown separately in reports
      ✔ One failure doesn't abort the others
      ✔ Easy to add more test cases — just add to the list

    To run only a specific parameter:
        pytest "tests/test_posts/test_posts_crud.py::test_get_post_by_valid_id[1]"
    """
    with allure.step(f"GET /posts/{post_id}"):
        response = posts_api.get_post(post_id)

    with allure.step("Assert 200 OK and correct post ID"):
        assert_status_code(response.status_code, 200)
        post = response.json()
        assert post["id"] == post_id, f"Returned post ID {post['id']} ≠ requested {post_id}"

    with allure.step("Validate response against Pydantic model"):
        # CONCEPT: Pydantic model validation — raises ValidationError if schema is wrong
        validated = Post(**post)
        assert validated.id == post_id


@allure.feature("Posts API")
@allure.story("Get Single Post — Negative Cases")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.negative
@pytest.mark.posts
@pytest.mark.parametrize(
    "post_id, expected_status",
    [
        (0,      404),   # zero ID  → not found
        (9999,   404),   # huge ID  → not found
        (-1,     404),   # negative → not found
    ],
    ids=["zero-id", "huge-id", "negative-id"],  # readable test IDs in output
)
def test_get_post_invalid_id_returns_404(posts_api: PostsAPI, post_id: int, expected_status: int):
    """
    CONCEPT: Parametrize with multiple arguments and custom IDs
    ────────────────────────────────────────────────────────────
    When parametrize receives a list of tuples, each tuple unpacks
    into the test function's parameters.

    `ids=` gives each test case a human-readable name instead of
    the default [0], [9999], [-1].

    CLI output will show:
        test_get_post_invalid_id_returns_404[zero-id]
        test_get_post_invalid_id_returns_404[huge-id]
        test_get_post_invalid_id_returns_404[negative-id]
    """
    with allure.step(f"GET /posts/{post_id} (expect {expected_status})"):
        response = posts_api.get_post(post_id)

    with allure.step(f"Assert HTTP {expected_status}"):
        assert_status_code(response.status_code, expected_status)


# =============================================================================
# TEST CLASS — Grouping related tests
# =============================================================================

@allure.feature("Posts API")
@pytest.mark.posts
@pytest.mark.crud
class TestPostsCRUD:
    """
    CONCEPT: Test Classes
    ─────────────────────
    Grouping tests in a class lets you:
      ✔ Share setup via class-level fixtures or class attributes
      ✔ Organise related test cases in reports
      ✔ Run only a class: pytest tests/ -k "TestPostsCRUD"

    Rules for test classes in pytest:
      - Class name MUST start with 'Test'
      - NO __init__ method (pytest creates instances itself)
      - Fixtures are injected as method parameters (not via self)
    """

    @allure.story("Create Post")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.smoke
    def test_create_post_returns_201(self, posts_api: PostsAPI, sample_post_payload: dict):
        """
        POST /posts → 201 Created.

        CONCEPT: AAA Pattern (Arrange, Act, Assert)
          Arrange: sample_post_payload fixture prepares the data
          Act:     we call posts_api.create_post(...)
          Assert:  we verify the status code and response body
        """
        # ── Arrange ───────────────────────────────────────────────────────────
        payload = sample_post_payload
        allure.attach(pretty_json(payload), "Request Payload", allure.attachment_type.JSON)

        # ── Act ───────────────────────────────────────────────────────────────
        with allure.step("POST /posts with valid payload"):
            response = posts_api.create_post(
                title=payload["title"],
                body=payload["body"],
                user_id=payload["userId"],
            )

        # ── Assert ────────────────────────────────────────────────────────────
        with allure.step("Assert 201 Created"):
            assert_status_code(response.status_code, 201)

        with allure.step("Assert response echoes submitted fields"):
            created = response.json()
            allure.attach(pretty_json(created), "Response Body", allure.attachment_type.JSON)
            assert created["title"] == payload["title"]
            assert created["body"] == payload["body"]
            assert created["userId"] == payload["userId"]
            assert "id" in created, "Response must include the new resource ID"

    @allure.story("Create Post")
    @pytest.mark.parametrize("payload", VALID_CREATE_PAYLOADS)
    def test_create_post_parametrized(self, posts_api: PostsAPI, payload: dict):
        """
        Parametrized creation test — creates posts for 3 different users.
        Shows combining a class method with @pytest.mark.parametrize.
        """
        response = posts_api.create_post(
            title=payload["title"],
            body=payload["body"],
            user_id=payload["userId"],
        )
        assert response.status_code == 201
        result = response.json()
        assert result["title"] == payload["title"]
        assert result["userId"] == payload["userId"]

    @allure.story("Update Post (PUT)")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_update_post_full_replacement(self, posts_api: PostsAPI):
        """
        PUT /posts/{id} → 200 OK with fully replaced data.

        NOTE — JSONPlaceholder constraint:
          POST /posts always returns a simulated id=101, but that resource is
          NOT actually stored. Attempting PUT /posts/101 returns 500.
          JSONPlaceholder only supports PUT on existing IDs 1–100.
          We therefore use a hardcoded known-good ID (1) for this test.

          In a real API, you would: create → capture real ID → PUT that ID.
          The `created_post` fixture still demonstrates fixture composition
          correctly; it just can't be used for PUT/DELETE on JSONPlaceholder.
        """
        post_id = 1  # Use a real persisted post (JSONPlaceholder IDs: 1–100)

        new_data = {
            "title": "Completely Replaced Title",
            "body": "Completely replaced body content",
            "user_id": 5,
        }

        with allure.step(f"PUT /posts/{post_id}"):
            response = posts_api.update_post(post_id=post_id, **new_data)

        with allure.step("Assert 200 OK and updated fields"):
            assert_status_code(response.status_code, 200)
            updated = response.json()
            assert updated["title"] == new_data["title"]
            assert updated["body"] == new_data["body"]

    @allure.story("Partial Update (PATCH)")
    @pytest.mark.parametrize("post_id,patch_data", PATCH_CASES)
    def test_patch_post(self, posts_api: PostsAPI, post_id: int, patch_data: dict):
        """
        PATCH /posts/{id} → 200 OK with only the provided field(s) changed.
        Runs 3 parametrized cases covering title-only, body-only, both.
        """
        with allure.step(f"PATCH /posts/{post_id} with {list(patch_data.keys())}"):
            response = posts_api.patch_post(post_id, **patch_data)

        with allure.step("Assert 200 and patched fields match"):
            assert_status_code(response.status_code, 200)
            result = response.json()
            for key, value in patch_data.items():
                assert result.get(key) == value, (
                    f"Field '{key}': expected '{value}', got '{result.get(key)}'"
                )

    @allure.story("Delete Post")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_post_returns_200(self, posts_api: PostsAPI):
        """
        DELETE /posts/{id} → 200 OK and empty body.
        JSONPlaceholder simulates deletion and returns {} with status 200.
        """
        with allure.step("DELETE /posts/1"):
            response = posts_api.delete_post(1)

        with allure.step("Assert 200 and empty body"):
            assert_status_code(response.status_code, 200)
            assert response.json() == {}, "Deleted resource should return empty body"


# =============================================================================
# FILTERING / QUERY PARAMETER TESTS
# =============================================================================

@allure.feature("Posts API")
@allure.story("Filter Posts by User")
@pytest.mark.regression
@pytest.mark.posts
@pytest.mark.parametrize("user_id, expected_count", [
    (1, 10),
    (2, 10),
    (3, 10),
], ids=["user-1", "user-2", "user-3"])
def test_get_posts_by_user_id(posts_api: PostsAPI, user_id: int, expected_count: int):
    """
    GET /posts?userId={id} → filtered list of posts.
    Each user on JSONPlaceholder has exactly 10 posts.
    """
    with allure.step(f"GET /posts?userId={user_id}"):
        response = posts_api.get_posts_by_user(user_id)

    with allure.step(f"Assert {expected_count} posts returned"):
        assert_status_code(response.status_code, 200)
        posts = response.json()
        assert len(posts) == expected_count, (
            f"Expected {expected_count} posts for userId={user_id}, got {len(posts)}"
        )
        # Verify every returned post belongs to this user
        for post in posts:
            assert post["userId"] == user_id


@allure.feature("Posts API")
@allure.story("Post Comments — Nested Resource")
@pytest.mark.regression
@pytest.mark.posts
def test_get_comments_for_post(posts_api: PostsAPI):
    """
    GET /posts/1/comments → nested sub-resource.
    Each post on JSONPlaceholder has exactly 5 comments.
    """
    with allure.step("GET /posts/1/comments"):
        response = posts_api.get_post_comments(1)

    with allure.step("Assert 200 and 5 comments"):
        assert_status_code(response.status_code, 200)
        comments = response.json()
        assert isinstance(comments, list)
        assert len(comments) == 5

    with allure.step("Validate comment schema"):
        for comment in comments:
            assert_response_schema(comment, ["id", "postId", "name", "email", "body"])
            assert comment["postId"] == 1


# =============================================================================
# SKIP / XFAIL EXAMPLES
# =============================================================================

@pytest.mark.skip(reason="Placeholder: auth not implemented in JSONPlaceholder")
@pytest.mark.posts
def test_create_post_requires_auth(posts_api: PostsAPI):
    """
    CONCEPT: @pytest.mark.skip
    ──────────────────────────
    Unconditionally skips this test. Use when:
      - Feature not yet implemented
      - Test environment doesn't support this case
      - Temporarily disabled while fixing a bug

    Shows as 's' (skipped) in test output.
    """
    response = posts_api.post("/posts", json={"title": "Unauthorized"})
    assert response.status_code == 401


@pytest.mark.skipif(
    condition=False,  # change to True to activate the skip
    reason="Skipped when running against production environment",
)
@pytest.mark.posts
def test_conditional_skip_example(posts_api: PostsAPI):
    """
    CONCEPT: @pytest.mark.skipif
    ─────────────────────────────
    Conditionally skip based on any Python expression.

    Real-world usage:
        @pytest.mark.skipif(
            settings.environment == "prod",
            reason="Destructive test — not safe on production"
        )
    """
    response = posts_api.get_post(1)
    assert response.status_code == 200


@pytest.mark.xfail(
    reason="JSONPlaceholder always returns 201 even for malformed data",
    strict=False,  # strict=True would make a passing xfail count as FAILURE
)
@pytest.mark.negative
@pytest.mark.posts
def test_create_post_with_missing_fields_xfail(posts_api: PostsAPI):
    """
    CONCEPT: @pytest.mark.xfail (Expected Failure)
    ────────────────────────────────────────────────
    Use when you KNOW the test currently fails but want to track it
    without blocking the CI pipeline.

    Results:
      xfail  → expected to fail, and it did    (shown as 'x', not 'F')
      xpass  → expected to fail, but it passed (shown as 'X')

    Real-world usage: marking known bugs while they are being fixed.
    """
    response = posts_api.post("/posts", json={})  # empty body
    assert response.status_code == 400  # JSONPlaceholder returns 201, so this xfails

"""
tests/test_comments/test_comments.py — Tests for /comments endpoint
=====================================================================
CONCEPTS DEMONSTRATED:
  ✔ pytest.raises — asserting exceptions are raised
  ✔ allure.title for overriding test display names
  ✔ @pytest.fixture at test-module level (local fixture)
  ✔ Testing email field format validation
"""

import pytest
import allure

from src.api.comments_api import CommentsAPI
from src.api.base_client import APIError
from src.utils.helpers import assert_status_code, assert_response_schema
from src.utils.logger import get_logger

log = get_logger(__name__)

# ── Module-local fixture (only available in THIS file) ────────────────────────

@pytest.fixture(scope="module")
def first_comment(comments_api: CommentsAPI) -> dict:
    """
    MODULE-local fixture defined directly in a test file.

    CONCEPT: You can define fixtures in test files (not just conftest.py).
    These fixtures are only available to tests in the same file.
    For fixtures shared across files, put them in conftest.py.
    """
    response = comments_api.get_comment(1)
    assert response.status_code == 200
    return response.json()


# ── Tests ─────────────────────────────────────────────────────────────────────

@allure.feature("Comments API")
@allure.story("List Comments")
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.smoke
@pytest.mark.comments
def test_get_all_comments_returns_500_items(comments_api: CommentsAPI):
    """GET /comments → 500 comment objects."""
    response = comments_api.get_all_comments()
    assert_status_code(response.status_code, 200)
    comments = response.json()
    assert len(comments) == 500


@allure.feature("Comments API")
@allure.story("Comment Schema")
@allure.title("Each comment has required schema fields and valid email")  # custom title in Allure
@pytest.mark.regression
@pytest.mark.comments
def test_comment_schema_includes_email(first_comment: dict):
    """
    CONCEPT: allure.title
    ─────────────────────
    @allure.title overrides the test function name in the Allure report.
    Use it to write a more descriptive display name.

    Validates that each comment has an 'email' field that looks like an email.
    """
    required_keys = ["id", "postId", "name", "email", "body"]
    assert_response_schema(first_comment, required_keys)

    # Basic email format check (contains '@' and '.')
    email = first_comment["email"]
    assert "@" in email and "." in email, f"Invalid email format: '{email}'"


@allure.feature("Comments API")
@allure.story("Filter Comments by Post")
@pytest.mark.regression
@pytest.mark.comments
@pytest.mark.parametrize("post_id,expected_count", [
    (1, 5),
    (5, 5),
    (10, 5),
], ids=["post-1", "post-5", "post-10"])
def test_filter_comments_by_post_id(comments_api: CommentsAPI, post_id: int, expected_count: int):
    """
    GET /comments?postId={id} → exactly 5 comments per post.
    Each post on JSONPlaceholder has exactly 5 comments.
    """
    with allure.step(f"GET /comments?postId={post_id}"):
        response = comments_api.get_comments_for_post(post_id)

    with allure.step(f"Assert {expected_count} comments returned"):
        assert_status_code(response.status_code, 200)
        comments = response.json()
        assert len(comments) == expected_count

    with allure.step("Assert all comments belong to the requested post"):
        for comment in comments:
            assert comment["postId"] == post_id


@allure.feature("Comments API")
@allure.story("Negative Cases")
@pytest.mark.negative
@pytest.mark.comments
def test_get_nonexistent_comment_returns_404(comments_api: CommentsAPI):
    """
    GET /comments/99999 → 404 Not Found.
    """
    response = comments_api.get_comment(99999)
    assert_status_code(response.status_code, 404)


@allure.feature("Comments API")
@allure.story("APIError Exception")
@pytest.mark.negative
@pytest.mark.comments
def test_api_error_raised_on_404(comments_api: CommentsAPI):
    """
    CONCEPT: pytest.raises
    ─────────────────────────
    pytest.raises() is a context manager that asserts a specific exception
    is raised. If the exception is NOT raised, the test FAILS.

    When we use `expected_status=200` in our API call but the server
    returns 404, our BaseAPIClient raises APIError.

    You can also inspect the exception value:
        with pytest.raises(APIError) as exc_info:
            ...
        assert exc_info.value.status_code == 404
        assert "404" in str(exc_info.value)
    """
    with allure.step("Call API with expected_status=200, but server returns 404"):
        with pytest.raises(APIError) as exc_info:
            comments_api._request(
                "GET",
                "/comments/99999",
                expected_status=200,  # we EXPECT 200 but get 404 → APIError raised
            )

    with allure.step("Verify the exception contains the 404 status code"):
        error = exc_info.value
        assert error.status_code == 404, f"Expected status 404, got {error.status_code}"
        assert "404" in str(error)

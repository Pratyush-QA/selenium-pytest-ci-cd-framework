"""
tests/test_users/test_users.py — Tests for /users endpoint
============================================================
CONCEPTS DEMONSTRATED:
  ✔ Using module-scoped fixture (all_users) from root conftest
  ✔ Allure severity levels
  ✔ Nested Pydantic model validation (User → Address → Company)
  ✔ Testing nested sub-resources (/users/{id}/posts, /todos, /albums)
  ✔ pytest.raises for exception testing
"""

import pytest
import allure

from src.api.users_api import UsersAPI
from src.models.user_model import User
from src.utils.helpers import assert_status_code, assert_response_schema, pretty_json
from src.utils.logger import get_logger

log = get_logger(__name__)

# ── Module-level constants ────────────────────────────────────────────────────
EXPECTED_TOTAL_USERS = 10
VALID_USER_IDS = [1, 3, 5, 7, 10]


@allure.feature("Users API")
@allure.story("List Users")
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.smoke
@pytest.mark.users
def test_get_all_users_returns_200_and_10_users(users_api: UsersAPI):
    """
    Smoke test: /users endpoint is up and returns exactly 10 users.
    """
    with allure.step("GET /users"):
        response = users_api.get_all_users()

    with allure.step("Assert 200 and count"):
        assert_status_code(response.status_code, 200)
        users = response.json()
        assert isinstance(users, list)
        assert len(users) == EXPECTED_TOTAL_USERS


@allure.feature("Users API")
@allure.story("User Schema Validation")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.regression
@pytest.mark.users
def test_user_schema_pydantic_validation(all_users: list[dict]):
    """
    CONCEPT: Pydantic model validation for every user in the list.

    Each user is parsed through the User Pydantic model. If any user
    has wrong types or missing required fields, ValidationError is raised.

    This is more powerful than checking keys manually because it also
    validates data types, nesting, and constraints (e.g. min_length).
    """
    for user_data in all_users:
        with allure.step(f"Validate user id={user_data.get('id')}"):
            user = User(**user_data)
            assert user.id is not None
            assert user.email  # non-empty string
            assert user.name   # non-empty string


@allure.feature("Users API")
@allure.story("Get Single User")
@pytest.mark.regression
@pytest.mark.users
@pytest.mark.parametrize("user_id", VALID_USER_IDS)
def test_get_user_by_id(users_api: UsersAPI, user_id: int):
    """Parametrized: GET /users/{id} for multiple valid IDs."""
    with allure.step(f"GET /users/{user_id}"):
        response = users_api.get_user(user_id)

    assert_status_code(response.status_code, 200)
    user = response.json()

    with allure.step("Assert correct user returned"):
        assert user["id"] == user_id
        assert_response_schema(user, ["id", "name", "username", "email"])

    with allure.step("Assert nested address and company objects"):
        assert "address" in user
        assert "city" in user["address"]
        assert "company" in user
        assert "name" in user["company"]


@allure.feature("Users API")
@allure.story("User Sub-resources")
@pytest.mark.regression
@pytest.mark.users
@pytest.mark.parametrize("user_id,expected_posts", [(1, 10), (2, 10), (3, 10)])
def test_user_has_posts(users_api: UsersAPI, user_id: int, expected_posts: int):
    """
    GET /users/{id}/posts → nested sub-resource.
    Verifies each user has the expected number of posts.
    """
    response = users_api.get_user_posts(user_id)
    assert_status_code(response.status_code, 200)
    posts = response.json()
    assert len(posts) == expected_posts
    for post in posts:
        assert post["userId"] == user_id


@allure.feature("Users API")
@allure.story("User Sub-resources")
@pytest.mark.regression
@pytest.mark.users
def test_user_todos_sub_resource(users_api: UsersAPI):
    """GET /users/1/todos → returns todos for user 1."""
    response = users_api.get_user_todos(1)
    assert_status_code(response.status_code, 200)
    todos = response.json()
    assert isinstance(todos, list)
    assert len(todos) > 0
    for todo in todos:
        assert todo["userId"] == 1
        assert "completed" in todo


@allure.feature("Users API")
@allure.story("Negative Cases")
@pytest.mark.negative
@pytest.mark.users
@pytest.mark.parametrize("user_id", [0, 999, -5])
def test_get_nonexistent_user_returns_404(users_api: UsersAPI, user_id: int):
    """
    Negative: non-existent user IDs should return 404.
    """
    response = users_api.get_user(user_id)
    assert_status_code(response.status_code, 404)

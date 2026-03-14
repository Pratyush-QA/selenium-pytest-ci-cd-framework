"""
tests/conftest.py — ROOT conftest (applies to ALL tests)
=========================================================
CONCEPT: conftest.py is pytest's magic configuration file.
  - pytest automatically discovers and loads it before running tests
  - Fixtures defined here are available to ALL tests in the directory
    and ALL sub-directories (unless overridden)
  - Hooks defined here affect the entire test session

SCOPE HIERARCHY (important!):
  session  → created ONCE for the entire test run (most shared/expensive)
  package  → created once per package directory
  module   → created once per test file
  class    → created once per test class
  function → created fresh for every single test (default — most isolated)

FIXTURE RESOLUTION ORDER (innermost wins):
  tests/test_posts/conftest.py  →  can override fixtures from
  tests/conftest.py             →  which can override fixtures from
  conftest.py (root)

TIP: Run `pytest --fixtures` to list all available fixtures and
     where they are defined.
"""

import json
import logging
import pytest
import allure

from config.settings import settings
from src.api.posts_api import PostsAPI
from src.api.users_api import UsersAPI
from src.api.todos_api import TodosAPI
from src.api.comments_api import CommentsAPI
from src.utils.logger import get_logger

log = get_logger(__name__)


# =============================================================================
# SESSION-SCOPED FIXTURES
# Created once for the entire test run — ideal for expensive setup like
# authentication, database connections, or (here) API client instances.
# =============================================================================

@pytest.fixture(scope="session")
def posts_api() -> PostsAPI:
    """
    SESSION scope: one PostsAPI instance shared across ALL tests.

    CONCEPT: session scope is great for API clients because:
      1. The client is stateless (each call is independent)
      2. Creating an HTTP session is slightly expensive
      3. We want connection pooling across tests

    The `yield` keyword separates setup (before) from teardown (after).
    Everything before yield = setup, everything after = teardown.
    """
    log.info("📦 [session] Creating PostsAPI client")
    client = PostsAPI()
    yield client
    # Teardown: close the HTTP session after ALL tests finish
    log.info("🔒 [session] Closing PostsAPI client")
    client.close()


@pytest.fixture(scope="session")
def users_api() -> UsersAPI:
    """SESSION scope: one UsersAPI instance for the whole test run."""
    log.info("📦 [session] Creating UsersAPI client")
    client = UsersAPI()
    yield client
    log.info("🔒 [session] Closing UsersAPI client")
    client.close()


@pytest.fixture(scope="session")
def todos_api() -> TodosAPI:
    """SESSION scope: one TodosAPI instance for the whole test run."""
    log.info("📦 [session] Creating TodosAPI client")
    client = TodosAPI()
    yield client
    log.info("🔒 [session] Closing TodosAPI client")
    client.close()


@pytest.fixture(scope="session")
def comments_api() -> CommentsAPI:
    """SESSION scope: one CommentsAPI instance for the whole test run."""
    log.info("📦 [session] Creating CommentsAPI client")
    client = CommentsAPI()
    yield client
    log.info("🔒 [session] Closing CommentsAPI client")
    client.close()


# =============================================================================
# MODULE-SCOPED FIXTURES
# Created once per test file. Good for data loaded once per test module.
# =============================================================================

@pytest.fixture(scope="module")
def all_posts(posts_api: PostsAPI) -> list[dict]:
    """
    MODULE scope: fetch all posts once and share across tests in a module.

    CONCEPT: Use module scope when multiple tests in a file need the same
    expensive data — avoids calling the API once per test.
    """
    log.info("📡 [module] Fetching all posts for module-level tests")
    response = posts_api.get_all_posts()
    assert response.status_code == 200, "Pre-condition failed: could not load posts"
    data = response.json()
    log.info("✅ [module] Loaded %d posts", len(data))
    return data


@pytest.fixture(scope="module")
def all_users(users_api: UsersAPI) -> list[dict]:
    """MODULE scope: fetch all users once per module."""
    response = users_api.get_all_users()
    assert response.status_code == 200
    return response.json()


# =============================================================================
# FUNCTION-SCOPED FIXTURES  (default scope)
# Created fresh for every test. Ensures test isolation.
# =============================================================================

@pytest.fixture
def sample_post_payload() -> dict:
    """
    FUNCTION scope (default): fresh payload dict for each test.

    CONCEPT: Function scope guarantees tests cannot share state through
    fixtures. Mutating this dict in one test won't affect another test.
    """
    return {
        "title": "Pytest Framework Post",
        "body": "This post was created by the automated test framework",
        "userId": 1,
    }


@pytest.fixture
def sample_todo_payload() -> dict:
    """FUNCTION scope: fresh todo payload for each test."""
    return {
        "title": "Complete pytest framework tutorial",
        "completed": False,
        "userId": 1,
    }


@pytest.fixture
def created_post(posts_api: PostsAPI, sample_post_payload: dict) -> dict:
    """
    FUNCTION scope: create a post before the test and ensure it exists.

    CONCEPT: Fixtures can depend on other fixtures — pytest resolves the
    dependency graph automatically. Here we use both `posts_api` (session)
    and `sample_post_payload` (function) as inputs.

    This fixture is a good example of "arrange" in the AAA pattern:
      Arrange → this fixture creates the resource
      Act     → the test calls update/delete/etc.
      Assert  → the test checks the result
    """
    log.info("🛠  [function] Creating a post for test")
    response = posts_api.create_post(
        title=sample_post_payload["title"],
        body=sample_post_payload["body"],
        user_id=sample_post_payload["userId"],  # payload key 'userId' → method param 'user_id'
    )
    assert response.status_code == 201, "Pre-condition failed: could not create test post"
    post = response.json()
    log.info("✅ [function] Post created with id=%s", post.get("id"))
    return post


# =============================================================================
# PYTEST HOOKS
# Hooks are special functions that pytest calls at specific points in
# the test lifecycle. They let you add custom behaviour globally.
# Official docs: https://docs.pytest.org/en/stable/reference/fixtures.html#conftest-py
# =============================================================================

def pytest_configure(config):
    """
    HOOK: Called once after command-line arguments are parsed.
    Use this to register dynamic markers or set up Allure environment info.

    CONCEPT: pytest_configure runs before any test collection. It's the
    right place to set up framework-level configuration.
    """
    log.info("🔧 pytest_configure: framework starting | env=%s | base_url=%s",
             settings.environment, settings.base_url)


def pytest_sessionstart(session):
    """
    HOOK: Called at the very beginning of the test session (before collection).
    Use for global setup like creating report directories.
    """
    log.info("🚀 Test session started | env=%s", settings.environment)


def pytest_sessionfinish(session, exitstatus):
    """
    HOOK: Called at the very end of the test session (after all tests run).
    Use for cleanup, sending notifications, or generating summary reports.

    exitstatus:
      0 = all tests passed
      1 = some tests failed
      2 = test execution was interrupted
      3 = internal error
      4 = no tests collected
      5 = no tests ran (all deselected)
    """
    status_map = {0: "✅ PASSED", 1: "❌ FAILED", 2: "⚠️ INTERRUPTED"}
    status_str = status_map.get(exitstatus, f"code={exitstatus}")
    log.info("🏁 Test session finished | result=%s", status_str)


def pytest_runtest_logreport(report):
    """
    HOOK: Called after each test phase (setup, call, teardown).
    Use this to add custom logging or integrate with external systems.

    CONCEPT: The report object has:
      report.nodeid   → "tests/test_posts/test_posts_crud.py::test_get_post"
      report.when     → "setup" | "call" | "teardown"
      report.outcome  → "passed" | "failed" | "skipped"
      report.duration → time in seconds
    """
    if report.when == "call":
        if report.failed:
            log.error("❌ FAILED: %s (%.2fs)", report.nodeid, report.duration)
        elif report.passed:
            log.debug("✅ passed: %s (%.2fs)", report.nodeid, report.duration)
        elif report.skipped:
            log.warning("⏭  skipped: %s", report.nodeid)


def pytest_collection_modifyitems(config, items):
    """
    HOOK: Called after test collection, before execution.
    Use to reorder, deselect, or add markers to collected tests.

    CONCEPT: This hook is powerful for:
      - Adding a 'slow' marker automatically to tests that match a pattern
      - Sorting tests by name or marker
      - Skipping tests based on environment
    """
    # Example: auto-skip tests marked @pytest.mark.slow in fast mode
    # You could control this with a --fast CLI flag
    # for item in items:
    #     if "slow" in item.keywords and config.getoption("--fast", default=False):
    #         item.add_marker(pytest.mark.skip(reason="Skipped in fast mode"))
    pass

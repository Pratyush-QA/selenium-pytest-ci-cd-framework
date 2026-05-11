"""
src/utils/helpers.py — Reusable test helper functions
======================================================
Pure utility functions with no side-effects. These are used inside
tests and fixtures to keep the test code clean and readable.
"""

import json
import time
from typing import Any


def assert_response_schema(response_data: dict, required_keys: list[str]) -> None:
    """
    Assert that a response dictionary contains all required keys.

    CONCEPT: Schema validation helpers centralise repetitive assertions,
    making test code shorter and failures more descriptive.

    Args:
        response_data: Parsed JSON response as dict.
        required_keys: List of keys that must be present.

    Raises:
        AssertionError: With a descriptive message if any key is missing.

    Example:
        assert_response_schema(post, ["id", "title", "body", "userId"])
    """
    missing = [key for key in required_keys if key not in response_data]
    assert not missing, (
        f"Response is missing required keys: {missing}\n"
        f"Actual keys: {list(response_data.keys())}"
    )


def assert_status_code(actual: int, expected: int) -> None:
    """
    Assert HTTP status code with a clear failure message.

    Args:
        actual: Status code returned by the API.
        expected: Status code we expect.
    """
    assert actual == expected, (
        f"Expected HTTP {expected}, got HTTP {actual}"
    )


def pretty_json(data: Any) -> str:
    """
    Return a nicely formatted JSON string for logging / Allure attachments.

    Args:
        data: Any JSON-serialisable Python object.

    Returns:
        Indented JSON string.
    """
    return json.dumps(data, indent=2, ensure_ascii=False)


def generate_post_payload(
    title: str = "Test Post",
    body: str = "Automated test body",
    user_id: int = 1,
) -> dict:
    """
    Build a valid POST /posts request payload.

    CONCEPT: Factory functions produce test data, keeping test bodies
    free of repetitive dict literals.
    """
    return {"title": title, "body": body, "userId": user_id}


def generate_todo_payload(
    title: str = "Test Todo",
    completed: bool = False,
    user_id: int = 1,
) -> dict:
    """Build a valid POST /todos request payload."""
    return {"title": title, "completed": completed, "userId": user_id}


def retry(func, retries: int = 3, delay: float = 1.0):
    """
    Retry a callable up to `retries` times with a `delay` between attempts.

    CONCEPT: Retry logic wraps flaky network calls so transient failures
    don't cause false test failures in CI/CD pipelines.

    Args:
        func: A zero-argument callable (lambda or partial).
        retries: Number of attempts.
        delay: Seconds to wait between retries.

    Returns:
        The return value of `func` on the first successful call.

    Raises:
        The last exception if all retries are exhausted.

    Example:
        response = retry(lambda: api.get_post(1))
    """
    last_exc: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            return func()
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            if attempt < retries:
                time.sleep(delay)
    raise last_exc  # type: ignore[misc]


def validate_pagination_headers(headers: dict) -> None:
    """
    Check common pagination response headers are present.
    JSONPlaceholder doesn't return real pagination headers, but this
    helper demonstrates the pattern for real APIs.
    """
    # For APIs that support pagination, you'd check X-Total-Count, Link, etc.
    # We include this as an example pattern.
    pass


def get_ids_from_list(items: list[dict], key: str = "id") -> list[int]:
    """Extract all IDs from a list of resource dicts."""
    return [item[key] for item in items if key in item]

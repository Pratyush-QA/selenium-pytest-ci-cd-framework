"""
src/utils/helpers.py — Reusable UI test helper utilities
"""

import time
from pathlib import Path
from datetime import datetime


def timestamp() -> str:
    """Return a timestamp string safe for use in filenames."""
    return datetime.now().strftime("%Y%m%d_%H%M%S_%f")


def screenshot_name(test_name: str) -> str:
    """Generate a unique screenshot filename from the test name."""
    safe = test_name.replace("::", "_").replace("/", "_").replace(" ", "_")
    return f"{safe}_{timestamp()}"


def wait_for_condition(condition_fn, timeout: float = 10.0, poll: float = 0.5) -> bool:
    """
    Poll a zero-arg callable until it returns truthy or timeout is reached.

    Use this for conditions Selenium's EC doesn't cover.

    Args:
        condition_fn: A callable that returns truthy when condition is met.
        timeout: Max seconds to wait.
        poll: How often to check (seconds).

    Returns:
        True if condition met, False if timed out.
    """
    end_time = time.time() + timeout
    while time.time() < end_time:
        if condition_fn():
            return True
        time.sleep(poll)
    return False

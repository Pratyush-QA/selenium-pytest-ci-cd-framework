"""
src/api/base_client.py — Base HTTP client for the entire framework
==================================================================
CONCEPT: A BaseAPIClient encapsulates all raw HTTP logic (session management,
headers, logging, retry, response parsing) so individual API clients only
need to define the endpoints they call — not how HTTP works.

Benefits:
  ✔ Single place to change auth headers, base URL, or timeout
  ✔ Consistent logging for every request/response
  ✔ Built-in retry logic for transient network errors
  ✔ Clean error messages when something goes wrong

All other API clients (PostsAPI, UsersAPI, etc.) inherit from this class.
"""

import time
from typing import Any, Optional

import requests
from requests import Response, Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config.settings import settings
from src.utils.logger import get_logger

log = get_logger(__name__)


class APIError(Exception):
    """
    Custom exception raised when an API call returns an unexpected status.

    CONCEPT: Custom exceptions let you catch API-level failures separately
    from network errors (ConnectionError, Timeout) in tests:

        with pytest.raises(APIError) as exc_info:
            api.get_post(id=99999)
        assert exc_info.value.status_code == 404
    """

    def __init__(self, message: str, status_code: int = 0, response: Optional[Response] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response

    def __str__(self) -> str:
        return f"APIError(status={self.status_code}): {self.args[0]}"


class BaseAPIClient:
    """
    Base class providing a configured requests.Session with:
      - Default headers (Content-Type, Accept)
      - Automatic retry on connection errors and 5xx responses
      - Per-request logging (method, URL, status, elapsed time)
      - Helper methods: get, post, put, patch, delete
    """

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or settings.base_url).rstrip("/")
        self.timeout = settings.timeout
        self.session = self._create_session()
        log.debug("BaseAPIClient initialised → base_url=%s", self.base_url)

    # ── Session factory ───────────────────────────────────────────────────────
    def _create_session(self) -> Session:
        """
        Create a requests.Session with:
          - Default headers
          - Automatic HTTP retry (via urllib3 Retry adapter)

        CONCEPT: Using a Session (not requests.get/post directly) means:
          - Connection pooling → faster tests
          - Shared cookies/auth across multiple requests
          - One place to set headers for all requests
        """
        session = requests.Session()

        # Default headers applied to every request
        session.headers.update(
            {
                "Content-Type": settings.content_type,
                "Accept": settings.accept,
                "User-Agent": "pytest-api-framework/1.0",
            }
        )

        # ── Retry adapter ─────────────────────────────────────────────────────
        # Retry on connection errors and 5xx responses automatically.
        # This prevents false test failures from transient network issues.
        retry_strategy = Retry(
            total=settings.retry_count,
            backoff_factor=settings.retry_delay,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    # ── Low-level request dispatcher ──────────────────────────────────────────
    def _request(
        self,
        method: str,
        endpoint: str,
        *,
        params: Optional[dict] = None,
        json: Optional[Any] = None,
        headers: Optional[dict] = None,
        expected_status: Optional[int] = None,
    ) -> Response:
        """
        Send an HTTP request and return the raw Response object.

        Args:
            method: HTTP verb (GET, POST, PUT, PATCH, DELETE).
            endpoint: Path appended to base_url (e.g. "/posts/1").
            params: Query string parameters.
            json: Request body serialised as JSON.
            headers: Extra headers to merge for this request only.
            expected_status: If provided, raise APIError if status differs.

        Returns:
            requests.Response

        CONCEPT: Centralising _request() means every API call automatically
        gets logging and error checking — no need to repeat it in every test.
        """
        url = f"{self.base_url}{endpoint}"
        start = time.perf_counter()

        log.info("→ %s %s | params=%s | body=%s", method, url, params, json)

        response = self.session.request(
            method=method,
            url=url,
            params=params,
            json=json,
            headers=headers,
            timeout=self.timeout,
        )

        elapsed = (time.perf_counter() - start) * 1000  # ms
        log.info(
            "← %s %s | status=%d | elapsed=%.1fms",
            method,
            url,
            response.status_code,
            elapsed,
        )

        if expected_status is not None and response.status_code != expected_status:
            raise APIError(
                f"{method} {url} returned {response.status_code}, "
                f"expected {expected_status}. Body: {response.text[:500]}",
                status_code=response.status_code,
                response=response,
            )

        return response

    # ── Convenience methods ───────────────────────────────────────────────────
    def get(self, endpoint: str, **kwargs) -> Response:
        return self._request("GET", endpoint, **kwargs)

    def post(self, endpoint: str, **kwargs) -> Response:
        return self._request("POST", endpoint, **kwargs)

    def put(self, endpoint: str, **kwargs) -> Response:
        return self._request("PUT", endpoint, **kwargs)

    def patch(self, endpoint: str, **kwargs) -> Response:
        return self._request("PATCH", endpoint, **kwargs)

    def delete(self, endpoint: str, **kwargs) -> Response:
        return self._request("DELETE", endpoint, **kwargs)

    # ── Teardown ──────────────────────────────────────────────────────────────
    def close(self) -> None:
        """Close the underlying requests Session to free resources."""
        self.session.close()
        log.debug("BaseAPIClient session closed")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

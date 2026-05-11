"""
config/settings.py — Centralised settings loader
==================================================
Reads config.ini and exposes a single `settings` object used across
the entire framework.

CONCEPT: Using configparser + environment variables lets you switch
environments without changing any code — just set the ENV variable.

Usage:
    from config.settings import settings
    print(settings.base_url)     # https://jsonplaceholder.typicode.com
    print(settings.timeout)      # 10 (int, not string)
"""

import os
import configparser
from pathlib import Path

# ── Locate config.ini relative to this file ───────────────────────────────────
_CONFIG_FILE = Path(__file__).parent / "config.ini"

# ── Read which environment we are running in ─────────────────────────────────
# The ENV variable can be set in:
#   - your shell before running pytest
#   - a .env file (via python-dotenv)
#   - the CI/CD pipeline environment (GitHub Actions secrets/vars)
#   - the Docker Compose file (environment: section)
_ENV = os.getenv("ENV", "dev").lower()


class Settings:
    """
    Loads all config values for the current environment and provides
    typed attributes (int, str, etc.) for easy use in tests.

    CONCEPT: A central settings object is better than scattered os.getenv()
    calls because:
      1. One place to add/change config keys
      2. Type conversion happens once
      3. Missing keys cause an early, clear error
    """

    def __init__(self, env: str = "dev"):
        self._parser = configparser.ConfigParser()
        if not _CONFIG_FILE.exists():
            raise FileNotFoundError(f"Config file not found: {_CONFIG_FILE}")
        self._parser.read(_CONFIG_FILE)

        if env not in self._parser.sections():
            available = self._parser.sections()
            raise ValueError(
                f"Unknown environment '{env}'. Available: {available}"
            )

        self._env = env
        self._section = self._parser[env]
        self._common = self._parser["common"]

    # ── Environment info ─────────────────────────────────────────────────────
    @property
    def environment(self) -> str:
        return self._env

    # ── Network settings ─────────────────────────────────────────────────────
    @property
    def base_url(self) -> str:
        return self._section["base_url"].rstrip("/")

    @property
    def timeout(self) -> int:
        return int(self._section["timeout"])

    @property
    def retry_count(self) -> int:
        return int(self._section["retry_count"])

    @property
    def retry_delay(self) -> float:
        return float(self._section["retry_delay"])

    # ── Endpoints ─────────────────────────────────────────────────────────────
    @property
    def posts_endpoint(self) -> str:
        return self._section["posts_endpoint"]

    @property
    def users_endpoint(self) -> str:
        return self._section["users_endpoint"]

    @property
    def todos_endpoint(self) -> str:
        return self._section["todos_endpoint"]

    @property
    def comments_endpoint(self) -> str:
        return self._section["comments_endpoint"]

    # ── Logging ───────────────────────────────────────────────────────────────
    @property
    def log_level(self) -> str:
        return self._section["log_level"].upper()

    # ── Common / shared settings ─────────────────────────────────────────────
    @property
    def content_type(self) -> str:
        return self._common["content_type"]

    @property
    def accept(self) -> str:
        return self._common["accept"]

    @property
    def allure_dir(self) -> str:
        return self._common["allure_dir"]

    @property
    def html_report(self) -> str:
        return self._common["html_report"]

    def __repr__(self) -> str:
        return f"<Settings env={self._env} base_url={self.base_url}>"


# ── Singleton instance ────────────────────────────────────────────────────────
# Import this anywhere: `from config.settings import settings`
settings = Settings(env=_ENV)

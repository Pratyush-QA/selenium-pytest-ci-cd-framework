"""
config/settings.py — Centralised settings loader for the UI framework
======================================================================
Reads config.ini and exposes a typed `settings` singleton.

Usage:
    from config.settings import settings
    print(settings.base_url)       # https://the-internet.herokuapp.com
    print(settings.explicit_wait)  # 10 (int)
    print(settings.headless)       # False (bool)
"""

import os
import configparser
from pathlib import Path

_CONFIG_FILE = Path(__file__).parent / "config.ini"
_ENV = os.getenv("ENV", "dev").lower()


class Settings:
    def __init__(self, env: str = "dev"):
        self._parser = configparser.ConfigParser()
        if not _CONFIG_FILE.exists():
            raise FileNotFoundError(f"Config file not found: {_CONFIG_FILE}")
        self._parser.read(_CONFIG_FILE)

        if env not in self._parser.sections():
            raise ValueError(f"Unknown env '{env}'. Available: {self._parser.sections()}")

        self._env     = env
        self._section = self._parser[env]
        self._common  = self._parser["common"]

    @property
    def environment(self) -> str:
        return self._env

    # ── Browser / Driver ──────────────────────────────────────────────────────
    @property
    def base_url(self) -> str:
        return self._section["base_url"].rstrip("/")

    @property
    def browser(self) -> str:
        # Allow CLI/env override: BROWSER=firefox pytest
        return os.getenv("BROWSER", self._section["browser"]).lower()

    @property
    def headless(self) -> bool:
        # Allow CLI/env override: HEADLESS=true pytest
        env_val = os.getenv("HEADLESS")
        if env_val is not None:
            return env_val.lower() in ("true", "1", "yes")
        return self._section["headless"].lower() in ("true", "1", "yes")

    @property
    def driver_mode(self) -> str:
        return self._section.get("driver_mode", "selenium_manager")

    # ── Waits ─────────────────────────────────────────────────────────────────
    @property
    def implicit_wait(self) -> int:
        return int(self._section["implicit_wait"])

    @property
    def explicit_wait(self) -> int:
        return int(self._section["explicit_wait"])

    @property
    def page_load_timeout(self) -> int:
        return int(self._section["page_load_timeout"])

    # ── Paths ─────────────────────────────────────────────────────────────────
    @property
    def screenshot_dir(self) -> Path:
        path = Path(self._section["screenshot_dir"])
        path.mkdir(exist_ok=True)
        return path

    @property
    def allure_dir(self) -> str:
        return self._common["allure_dir"]

    @property
    def html_report(self) -> str:
        return self._common["html_report"]

    # ── Test credentials ──────────────────────────────────────────────────────
    @property
    def valid_username(self) -> str:
        return self._common["valid_username"]

    @property
    def valid_password(self) -> str:
        return self._common["valid_password"]

    @property
    def invalid_username(self) -> str:
        return self._common["invalid_username"]

    @property
    def invalid_password(self) -> str:
        return self._common["invalid_password"]

    def __repr__(self) -> str:
        return f"<Settings env={self._env} base_url={self.base_url} browser={self.browser}>"


# ── Singleton ─────────────────────────────────────────────────────────────────
settings = Settings(env=_ENV)

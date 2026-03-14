"""
src/utils/logger.py — Centralised logging setup
================================================
Creates a named logger with consistent formatting across the framework.
pytest also captures log output — this integrates with pytest's
--log-cli and log_file settings in pytest.ini.

Usage:
    from src.utils.logger import get_logger
    log = get_logger(__name__)
    log.info("Sending POST /posts")
    log.debug("Payload: %s", payload)
"""

import logging
import os
from pathlib import Path

# ── Ensure the logs/ directory exists ────────────────────────────────────────
_LOGS_DIR = Path(__file__).parents[2] / "logs"
_LOGS_DIR.mkdir(exist_ok=True)


def get_logger(name: str) -> logging.Logger:
    """
    Return a logger for the given module name.

    CONCEPT: Always use __name__ as the logger name so log messages
    include the full module path, making it easy to trace which file
    emitted a log line, e.g.:
        2024-01-01 12:00:00 [INFO] src.api.posts_api: GET /posts → 200
    """
    logger = logging.getLogger(name)

    # Avoid adding duplicate handlers if logger already configured
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # ── Console handler ───────────────────────────────────────────────────────
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_fmt = logging.Formatter(
        fmt="%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(console_fmt)

    # ── File handler ──────────────────────────────────────────────────────────
    file_handler = logging.FileHandler(_LOGS_DIR / "framework.log", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_fmt = logging.Formatter(
        fmt="%(asctime)s [%(levelname)-8s] %(name)s (%(filename)s:%(lineno)d): %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_fmt)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger

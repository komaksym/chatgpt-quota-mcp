"""Application service for the ChatGPT quota tool."""

from typing import Any

from .codex import read_rate_limits
from .quota import normalize_quota


def get_chatgpt_quota() -> dict[str, Any]:
    """Read the current Codex quota snapshot and return normalized tool output."""
    return normalize_quota(read_rate_limits())

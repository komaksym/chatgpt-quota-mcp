"""Normalize Codex App Server quota responses for MCP consumers."""

from collections.abc import Mapping
from typing import Any


def _normalize_window(name: str, window: Mapping[str, Any]) -> dict[str, Any]:
    """Convert one Codex quota window to the stable public tool shape."""
    used = float(window["usedPercent"])
    remaining = max(0.0, min(100.0, 100.0 - used))
    return {
        "name": name,
        "used_percent": used,
        "remaining_percent": remaining,
        "window_minutes": int(window["windowDurationMins"]),
        "resets_at": int(window["resetsAt"]),
    }


def normalize_quota(result: Mapping[str, Any]) -> dict[str, Any]:
    """Convert `account/rateLimits/read` result data to stable tool output."""
    limits_value = result.get("rateLimits")
    if not isinstance(limits_value, Mapping):
        raise ValueError("Codex quota response is missing rateLimits")
    limits: Mapping[str, Any] = limits_value

    windows: list[dict[str, Any]] = []
    for name in ("primary", "secondary"):
        window = limits.get(name)
        if window is None:
            continue
        if not isinstance(window, Mapping):
            raise ValueError(f"Codex quota window {name} is malformed")
        windows.append(_normalize_window(name, window))

    return {
        "source": "codex_app_server",
        "windows": windows,
        "rate_limit_reached_type": limits.get("rateLimitReachedType"),
        "individual_limit": limits.get("individualLimit"),
        "spend_control_reached": limits.get("spendControlReached"),
        "reset_credits": result.get("rateLimitResetCredits"),
    }

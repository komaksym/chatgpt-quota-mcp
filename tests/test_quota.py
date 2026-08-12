from chatgpt_quota_mcp.quota import normalize_quota


def test_normalize_quota_returns_available_windows_and_remaining_percent() -> None:
    """Normalize both Codex quota windows without assuming their durations."""
    result = {
        "rateLimits": {
            "primary": {
                "usedPercent": 25,
                "windowDurationMins": 300,
                "resetsAt": 1_786_543_200,
            },
            "secondary": {
                "usedPercent": 60.5,
                "windowDurationMins": 10_080,
                "resetsAt": 1_787_000_000,
            },
            "rateLimitReachedType": None,
            "individualLimit": {"amount": 100},
            "spendControlReached": False,
        },
        "rateLimitResetCredits": {"availableCount": 2, "credits": None},
    }

    assert normalize_quota(result) == {
        "source": "codex_app_server",
        "windows": [
            {
                "name": "primary",
                "used_percent": 25.0,
                "remaining_percent": 75.0,
                "window_minutes": 300,
                "resets_at": 1_786_543_200,
            },
            {
                "name": "secondary",
                "used_percent": 60.5,
                "remaining_percent": 39.5,
                "window_minutes": 10_080,
                "resets_at": 1_787_000_000,
            },
        ],
        "rate_limit_reached_type": None,
        "individual_limit": {"amount": 100},
        "spend_control_reached": False,
        "reset_credits": {"availableCount": 2, "credits": None},
    }


def test_normalize_quota_omits_missing_secondary_window() -> None:
    """Return only quota windows the Codex backend actually provides."""
    result = {
        "rateLimits": {
            "primary": {
                "usedPercent": 5,
                "windowDurationMins": 10_080,
                "resetsAt": 1_787_000_000,
            },
            "secondary": None,
            "rateLimitReachedType": None,
        },
        "rateLimitResetCredits": None,
    }

    normalized = normalize_quota(result)

    assert normalized["windows"] == [
        {
            "name": "primary",
            "used_percent": 5.0,
            "remaining_percent": 95.0,
            "window_minutes": 10_080,
            "resets_at": 1_787_000_000,
        }
    ]

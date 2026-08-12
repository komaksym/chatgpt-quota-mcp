from typing import Any

from chatgpt_quota_mcp import service


def test_get_chatgpt_quota_reads_and_normalizes_codex_snapshot(monkeypatch) -> None:
    """Keep Codex I/O outside the service while returning normalized quota data."""
    raw: dict[str, Any] = {
        "rateLimits": {
            "primary": {
                "usedPercent": 20,
                "windowDurationMins": 300,
                "resetsAt": 123,
            },
            "secondary": None,
        },
        "rateLimitResetCredits": None,
    }
    monkeypatch.setattr(service, "read_rate_limits", lambda: raw)

    result = service.get_chatgpt_quota()

    assert result["windows"][0]["remaining_percent"] == 80.0
    assert result["source"] == "codex_app_server"

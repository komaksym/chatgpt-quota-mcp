import sys
from pathlib import Path

import pytest

from chatgpt_quota_mcp.codex import CodexAppServerError, read_rate_limits


def _write_fake_server(path: Path, response_code: str) -> None:
    """Write a tiny JSONL app-server process used by subprocess tests."""
    path.write_text(
        "import json, sys\n"
        "init = json.loads(sys.stdin.readline())\n"
        "assert init['method'] == 'initialize'\n"
        "print(json.dumps({'id': init['id'], 'result': {'userAgent': 'fake'}}), flush=True)\n"
        "initialized = json.loads(sys.stdin.readline())\n"
        "assert initialized['method'] == 'initialized' and 'id' not in initialized\n"
        "req = json.loads(sys.stdin.readline())\n"
        "assert req['method'] == 'account/rateLimits/read'\n"
        + response_code
    )


def test_read_rate_limits_completes_handshake_and_ignores_notifications(tmp_path: Path) -> None:
    """Return the matching quota response even when a notification arrives first."""
    server = tmp_path / "fake_codex.py"
    _write_fake_server(
        server,
        "print(json.dumps({'method': 'account/rateLimits/updated', 'params': {}}), flush=True)\n"
        "print(json.dumps({'id': req['id'], 'result': {'rateLimits': {"
        "'primary': {'usedPercent': 25, 'windowDurationMins': 300, 'resetsAt': 123}, "
        "'secondary': None}}}), flush=True)\n",
    )

    result = read_rate_limits((sys.executable, "-S", str(server)), timeout_s=1.0)

    assert result["rateLimits"]["primary"]["usedPercent"] == 25


def test_read_rate_limits_raises_clean_error_for_json_rpc_failure(tmp_path: Path) -> None:
    """Surface a concise Codex error without exposing subprocess state."""
    server = tmp_path / "fake_codex_error.py"
    _write_fake_server(
        server,
        "print(json.dumps({'id': req['id'], 'error': {"
        "'code': -32000, 'message': 'not logged in'}}), flush=True)\n",
    )

    with pytest.raises(CodexAppServerError, match="not logged in"):
        read_rate_limits((sys.executable, "-S", str(server)), timeout_s=1.0)


def test_read_rate_limits_reports_missing_codex_executable() -> None:
    """Explain how to fix a missing Codex CLI instead of leaking OSError details."""
    with pytest.raises(CodexAppServerError, match="Codex CLI executable was not found"):
        read_rate_limits(("definitely-not-a-real-codex-command",), timeout_s=0.1)

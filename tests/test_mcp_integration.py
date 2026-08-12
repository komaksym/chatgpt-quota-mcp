"""End-to-end MCP protocol test using a fake Codex CLI backend."""

import asyncio
import os
import sys
from pathlib import Path

import pytest

pytest.importorskip("mcp")

from mcp import Client, StdioServerParameters  # noqa: E402
from mcp.client.stdio import stdio_client  # noqa: E402


def _write_fake_codex(path: Path) -> None:
    """Write an executable Codex stand-in that implements the required App Server RPCs."""
    path.write_text(
        f"#!{sys.executable}\n"
        "import json\n"
        "import sys\n"
        "assert sys.argv[1:] == ['app-server', '--stdio']\n"
        "init = json.loads(sys.stdin.readline())\n"
        "assert init['method'] == 'initialize'\n"
        "print(json.dumps({'id': init['id'], 'result': {'userAgent': 'fake'}}), flush=True)\n"
        "initialized = json.loads(sys.stdin.readline())\n"
        "assert initialized['method'] == 'initialized'\n"
        "req = json.loads(sys.stdin.readline())\n"
        "assert req['method'] == 'account/rateLimits/read'\n"
        "print(json.dumps({'id': req['id'], 'result': {'rateLimits': {"
        "'primary': {'usedPercent': 25, 'windowDurationMins': 300, 'resetsAt': 123}, "
        "'secondary': None, 'rateLimitReachedType': None}, "
        "'rateLimitResetCredits': None}}), flush=True)\n"
    )
    path.chmod(0o755)


def test_mcp_tool_reads_quota_through_stdio_protocol(tmp_path: Path) -> None:
    """Exercise MCP stdio -> service -> fake Codex App Server -> normalized result."""
    fake_codex = tmp_path / "codex"
    _write_fake_codex(fake_codex)
    env = os.environ.copy()
    env["PATH"] = f"{tmp_path}{os.pathsep}{env['PATH']}"

    async def exercise() -> None:
        """Connect with the real MCP client, list the tool, and call it once."""
        params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "chatgpt_quota_mcp.server"],
            env=env,
        )
        async with Client(stdio_client(params)) as client:
            tools = await client.list_tools()
            assert [tool.name for tool in tools.tools] == ["get_chatgpt_quota"]

            result = await client.call_tool("get_chatgpt_quota", {})
            assert result.structured_content is not None
            assert result.structured_content["windows"][0] == {
                "name": "primary",
                "used_percent": 25.0,
                "remaining_percent": 75.0,
                "window_minutes": 300,
                "resets_at": 123,
            }

    asyncio.run(exercise())

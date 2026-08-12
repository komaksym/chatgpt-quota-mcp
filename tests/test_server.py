import importlib
import sys
import types
from collections.abc import Callable
from typing import Any


def _load_server_with_fake_mcp(monkeypatch):
    """Import the server against a minimal MCPServer stand-in for unit tests."""
    server_module = types.ModuleType("mcp.server")

    class FakeMCPServer:
        """Record registered tools and whether stdio serving was started."""

        def __init__(self, name: str) -> None:
            """Create an empty fake MCP registry."""
            self.name = name
            self.tools: dict[str, Callable[..., Any]] = {}
            self.ran = False

        def tool(self):
            """Return a decorator that records a tool without wrapping it."""

            def register(fn: Callable[..., Any]) -> Callable[..., Any]:
                """Register and return the original tool function."""
                self.tools[fn.__name__] = fn
                return fn

            return register

        def run(self) -> None:
            """Record that the server entry point started the default stdio transport."""
            self.ran = True

    server_module.MCPServer = FakeMCPServer
    monkeypatch.setitem(sys.modules, "mcp", types.ModuleType("mcp"))
    monkeypatch.setitem(sys.modules, "mcp.server", server_module)
    sys.modules.pop("chatgpt_quota_mcp.server", None)
    return importlib.import_module("chatgpt_quota_mcp.server")


def test_server_exposes_exactly_one_quota_tool(monkeypatch) -> None:
    """Register one no-argument tool that delegates to the quota service."""
    server = _load_server_with_fake_mcp(monkeypatch)
    monkeypatch.setattr(server, "read_quota", lambda: {"windows": []})

    assert list(server.mcp.tools) == ["get_chatgpt_quota"]
    assert server.get_chatgpt_quota() == {"windows": []}


def test_main_runs_the_stdio_mcp_server(monkeypatch) -> None:
    """Start MCPServer using its default stdio transport."""
    server = _load_server_with_fake_mcp(monkeypatch)

    server.main()

    assert server.mcp.ran is True

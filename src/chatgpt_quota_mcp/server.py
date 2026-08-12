"""MCP entry point exposing the ChatGPT quota tool over stdio."""

from typing import Any

from mcp.server import MCPServer

from .service import get_chatgpt_quota as read_quota

mcp = MCPServer("ChatGPT Quota")


@mcp.tool()
def get_chatgpt_quota() -> dict[str, Any]:
    """Return current ChatGPT/Codex quota windows, remaining usage, and reset times."""
    return read_quota()


def main() -> None:
    """Run the MCP server using MCPServer's default stdio transport."""
    mcp.run()


if __name__ == "__main__":
    main()

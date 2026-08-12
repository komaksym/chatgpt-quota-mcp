# ChatGPT Quota MCP Design

## Goal

Expose one local MCP tool, `get_chatgpt_quota`, that reads the signed-in user's ChatGPT/Codex quota through the installed Codex CLI.

## Chosen approach

Use a small Python MCP v2 server over stdio. The tool starts `codex app-server --stdio`, performs the required `initialize` -> `initialized` handshake, calls `account/rateLimits/read`, normalizes the response, then terminates the child process.

This is preferred over:

1. ChatGPT UI automation: brittle and unnecessary when Codex exposes the quota as structured data.
2. Direct calls to undocumented ChatGPT backend endpoints: couples the project to private auth and backend details.

## Architecture

```text
ChatGPT plugin
    |
Secure MCP Tunnel
    |
stdio MCP server (`chatgpt-quota-mcp`)
    |
Codex adapter
    |
`codex app-server --stdio`
    |
`account/rateLimits/read`
```

## Components

- `quota.py`: pure normalization from Codex's rate-limit response to stable tool output.
- `codex.py`: subprocess and JSON-RPC protocol boundary for Codex App Server.
- `service.py`: orchestration between Codex I/O and normalization.
- `server.py`: MCP v2 `MCPServer` registration only; exposes the single tool and delegates to the service.

## Tool contract

`get_chatgpt_quota()` takes no arguments and returns:

```json
{
  "source": "codex_app_server",
  "windows": [
    {
      "name": "primary",
      "used_percent": 25,
      "remaining_percent": 75,
      "window_minutes": 300,
      "resets_at": 1786543200
    }
  ],
  "rate_limit_reached_type": null,
  "individual_limit": null,
  "spend_control_reached": null,
  "reset_credits": null
}
```

The implementation does not assume that primary means 5-hour or secondary means weekly. The server reports the actual `windowDurationMins` returned by Codex.

## Errors

- Missing `codex` executable: raise a short actionable MCP tool error.
- Codex JSON-RPC error: surface the method-level error without dumping environment variables or auth state.
- Timeout / early process exit / malformed protocol: surface a concise protocol error.
- Child process is always terminated after each tool call.

## Testing

TDD covers:

1. Normalization of one and two quota windows.
2. Codex handshake and ignoring unrelated notifications before the matching response.
3. Codex JSON-RPC errors and missing executable errors.
4. MCP tool registration.
5. A real MCP v2 stdio round trip using a fake Codex executable.
6. CI runs Ruff, mypy, pytest, and package build.

## Scope

No UI, database, OAuth layer, direct ChatGPT HTTP calls, daemon, caching, background polling, or Codex-CLI-absent fallback.

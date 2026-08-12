# ChatGPT Quota MCP

A single local MCP tool that lets ChatGPT read your current ChatGPT/Codex quota through your already signed-in Codex CLI.

```text
ChatGPT
   |
Secure MCP Tunnel
   |
get_chatgpt_quota (local MCP)
   |
codex app-server --stdio
   |
account/rateLimits/read
```

## What it returns

The server exposes one no-argument tool:

```text
get_chatgpt_quota()
```

Example result:

```json
{
  "source": "codex_app_server",
  "windows": [
    {
      "name": "primary",
      "used_percent": 25.0,
      "remaining_percent": 75.0,
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

The tool does not assume that `primary` means 5-hour or `secondary` means weekly. It reports the window duration Codex actually returns.

## Prerequisites

- Python 3.11+
- [`uv`](https://docs.astral.sh/uv/)
- Codex CLI available as `codex`
- Codex CLI already signed in to the ChatGPT account whose quota you want to read

Verify the last two with:

```bash
command -v codex
codex
```

## Install

```bash
git clone https://github.com/komaksym/chatgpt-quota-mcp.git
cd chatgpt-quota-mcp
uv sync --extra dev
```

## Test the quota locally first

This bypasses MCP and proves that the Codex quota read works on your machine:

```bash
uv run python -c 'from chatgpt_quota_mcp.service import get_chatgpt_quota; import json; print(json.dumps(get_chatgpt_quota(), indent=2))'
```

If that prints your quota, the Codex side is working.

## Connect it to ChatGPT

OpenAI Secure MCP Tunnel can launch a local stdio MCP command, so this project does not need an HTTP server or public port.

1. In OpenAI Platform tunnel settings, create a tunnel associated with the ChatGPT workspace you will use and obtain a `tunnel_id` plus runtime API key.
2. Install the current `tunnel-client` from OpenAI's tunnel settings/download instructions.
3. Configure the tunnel to launch this project's MCP executable:

```bash
export CONTROL_PLANE_API_KEY="sk-..."

TUNNEL_ID="tunnel_..."
MCP_COMMAND="$(pwd)/.venv/bin/chatgpt-quota-mcp"

tunnel-client init \
  --sample sample_mcp_stdio_local \
  --profile chatgpt-quota \
  --tunnel-id "$TUNNEL_ID" \
  --mcp-command "$MCP_COMMAND"

tunnel-client doctor --profile chatgpt-quota --explain
tunnel-client run --profile chatgpt-quota
```

Do not commit the runtime API key.

4. In ChatGPT, enable **Settings -> Security and login -> Developer mode**.
5. Open **ChatGPT Plugins**, press **+**, choose **Tunnel** under Connection, and select or paste your `tunnel_id`.
6. Confirm that ChatGPT discovers exactly one tool: `get_chatgpt_quota`.

Then ask:

> How much Codex quota do I have left?

## Development

```bash
uv sync --extra dev
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest
uv build
```

The test suite includes a real MCP stdio round trip backed by a fake Codex executable, so CI exercises the full local protocol chain without using a real account.

## Why this shape

The Codex App Server has a stable `account/rateLimits/read` method. Using that structured interface is smaller and less brittle than scraping ChatGPT UI text or calling undocumented ChatGPT backend endpoints.

## References

- [Codex App Server](https://github.com/openai/codex/blob/main/codex-rs/app-server/README.md)
- [OpenAI Secure MCP Tunnel](https://developers.openai.com/api/docs/guides/secure-mcp-tunnels)
- [Connect and test a ChatGPT plugin](https://developers.openai.com/plugins/deploy/connect-chatgpt)

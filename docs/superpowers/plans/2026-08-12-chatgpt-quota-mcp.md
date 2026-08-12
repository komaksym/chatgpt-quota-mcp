# ChatGPT Quota MCP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build one local MCP tool that returns ChatGPT/Codex quota from the installed, signed-in Codex CLI.

**Architecture:** A stdio MCP v2 server delegates to a small service. The service launches `codex app-server --stdio`, uses newline-delimited JSON-RPC for initialization and `account/rateLimits/read`, then normalizes the result into a stable tool schema.

**Tech Stack:** Python 3.11+, official MCP Python SDK v2, pytest, Ruff, mypy, uv.

## Global Constraints

- Work directly on `main`; do not open a PR.
- Smallest complete implementation only.
- No Codex-CLI-absent fallback.
- No UI or HTTP server.
- Every function has a useful docstring.
- Test-first development.

---

### Task 1: Pure quota normalization

**Files:**
- Create: `src/chatgpt_quota_mcp/quota.py`
- Test: `tests/test_quota.py`

**Interfaces:**
- Consumes: raw `dict[str, Any]` returned as the `result` of `account/rateLimits/read`.
- Produces: `normalize_quota(result: Mapping[str, Any]) -> dict[str, Any]`.

- [x] Write a failing test for primary/secondary window normalization and missing secondary window.
- [x] Run only `tests/test_quota.py` and confirm RED.
- [x] Implement the minimum normalizer.
- [x] Run `tests/test_quota.py` and confirm GREEN.

### Task 2: Codex App Server adapter

**Files:**
- Create: `src/chatgpt_quota_mcp/codex.py`
- Test: `tests/test_codex.py`

**Interfaces:**
- Consumes: command sequence, defaulting to `("codex", "app-server", "--stdio")`.
- Produces: `read_rate_limits(command: Sequence[str] = ..., timeout_s: float = 10.0) -> dict[str, Any]`.

- [x] Write a fake app-server test that requires `initialize`, accepts `initialized`, emits an unrelated notification, and then returns the quota response.
- [x] Run only the adapter test and confirm RED.
- [x] Implement subprocess lifecycle, JSONL writes, matching response reads, and cleanup.
- [x] Add tests for JSON-RPC error and missing executable, then implement the minimal errors.
- [x] Run `tests/test_codex.py` and confirm GREEN.

### Task 3: MCP tool and packaging

**Files:**
- Create: `src/chatgpt_quota_mcp/server.py`
- Create: `src/chatgpt_quota_mcp/service.py`
- Create: `src/chatgpt_quota_mcp/__init__.py`
- Create: `tests/test_server.py`
- Create: `tests/test_service.py`
- Create: `tests/test_mcp_integration.py`
- Create: `pyproject.toml`

**Interfaces:**
- Produces MCP tool `get_chatgpt_quota()` with no arguments.
- Console entry point: `chatgpt-quota-mcp`.

- [x] Write failing MCP/service tests before their production code.
- [x] Implement MCP v2 `MCPServer` stdio registration and console entry point.
- [x] Add a real SDK stdio integration test backed by a fake Codex executable.
- [x] Run the local test suite; the real-SDK integration runs in CI where dependencies are installed.

### Task 4: User setup and continuous validation

**Files:**
- Create: `README.md`
- Create: `.github/workflows/ci.yml`
- Create: `.gitignore`

**Interfaces:**
- Document `uv sync`, Codex auth precondition, direct local smoke test, Secure MCP Tunnel stdio command, and ChatGPT developer-mode connection.

- [x] Add setup instructions with no secrets committed.
- [x] Add CI commands: `ruff check .`, `ruff format --check .`, `mypy src`, `pytest`, and `uv build`.
- [x] Run local tests, compile check, and offline package build.
- [ ] Push to `main`, then inspect GitHub Actions and fix failures until green.

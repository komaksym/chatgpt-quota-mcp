"""Read ChatGPT quota through the local Codex App Server protocol."""

from __future__ import annotations

import json
import queue
import subprocess
import threading
import time
from collections.abc import Mapping, Sequence
from typing import IO, Any

DEFAULT_CODEX_COMMAND = ("codex", "app-server", "--stdio")


class CodexAppServerError(RuntimeError):
    """Raised when the Codex CLI or App Server protocol cannot return quota."""


def _write_message(stream: IO[str], message: Mapping[str, Any]) -> None:
    """Write one newline-delimited JSON-RPC message to Codex and flush it."""
    stream.write(json.dumps(message, separators=(",", ":")) + "\n")
    stream.flush()


def _enqueue_line(stream: IO[str], output: queue.Queue[str]) -> None:
    """Read one line from a pipe and place it on a queue for timeout handling."""
    output.put(stream.readline())


def _readline_with_timeout(stream: IO[str], timeout_s: float) -> str:
    """Read one pipe line while enforcing a timeout without relying on fd buffering."""
    output: queue.Queue[str] = queue.Queue(maxsize=1)
    reader = threading.Thread(
        target=_enqueue_line,
        args=(stream, output),
        daemon=True,
    )
    reader.start()
    try:
        return output.get(timeout=timeout_s)
    except queue.Empty as exc:
        raise CodexAppServerError("Timed out waiting for Codex App Server") from exc


def _read_matching_response(
    proc: subprocess.Popen[str], request_id: int, timeout_s: float
) -> dict[str, Any]:
    """Read JSONL messages until the response for `request_id` arrives."""
    if proc.stdout is None:
        raise CodexAppServerError("Codex App Server stdout is unavailable")

    deadline = time.monotonic() + timeout_s
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise CodexAppServerError("Timed out waiting for Codex App Server")

        line = _readline_with_timeout(proc.stdout, remaining)
        if not line:
            raise CodexAppServerError("Codex App Server exited before replying")

        try:
            message: Any = json.loads(line)
        except json.JSONDecodeError as exc:
            raise CodexAppServerError("Codex App Server returned malformed JSON") from exc

        if not isinstance(message, Mapping):
            raise CodexAppServerError("Codex App Server returned malformed JSON")
        if message.get("id") != request_id:
            continue

        error = message.get("error")
        if error is not None:
            detail = "unknown Codex error"
            if isinstance(error, Mapping):
                detail = str(error.get("message", detail))
            raise CodexAppServerError(f"Codex App Server error: {detail}")

        result = message.get("result")
        if not isinstance(result, dict):
            raise CodexAppServerError("Codex App Server response is missing a result")
        return result


def _stop_process(proc: subprocess.Popen[str]) -> None:
    """Terminate the short-lived Codex App Server without exposing its stderr."""
    if proc.poll() is not None:
        return
    proc.terminate()
    try:
        proc.wait(timeout=1.0)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=1.0)


def read_rate_limits(
    command: Sequence[str] = DEFAULT_CODEX_COMMAND, timeout_s: float = 10.0
) -> dict[str, Any]:
    """Fetch the raw `account/rateLimits/read` result from a signed-in Codex CLI."""
    try:
        proc = subprocess.Popen(
            tuple(command),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            bufsize=1,
        )
    except FileNotFoundError as exc:
        raise CodexAppServerError(
            "Codex CLI executable was not found; install Codex and ensure `codex` is on PATH"
        ) from exc

    try:
        if proc.stdin is None:
            raise CodexAppServerError("Codex App Server stdin is unavailable")

        _write_message(
            proc.stdin,
            {
                "method": "initialize",
                "id": 1,
                "params": {
                    "clientInfo": {
                        "name": "chatgpt_quota_mcp",
                        "title": "ChatGPT Quota MCP",
                        "version": "0.1.0",
                    }
                },
            },
        )
        _read_matching_response(proc, 1, timeout_s)
        _write_message(proc.stdin, {"method": "initialized"})
        _write_message(proc.stdin, {"method": "account/rateLimits/read", "id": 2})
        return _read_matching_response(proc, 2, timeout_s)
    finally:
        _stop_process(proc)

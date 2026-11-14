"""Shared safe helpers for tool adapters."""

from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any
from uuid import uuid4

from agent.logging_utils import log_tool
from agent.schemas import ToolResult


ROOT = Path(__file__).resolve().parents[2]


def demo_mode() -> bool:
    return os.getenv("DEMO_MODE", "true").lower() == "true"


def load_demo_state() -> dict[str, Any]:
    return json.loads((ROOT / "data" / "demo_state.json").read_text(encoding="utf-8"))


def result(tool: str, action, request_id: str | None = None) -> ToolResult:
    """Run a tool action and return a consistent error-safe response."""
    request_id = request_id or str(uuid4())
    started = time.perf_counter()
    try:
        data, evidence = action()
        item = ToolResult(tool=tool, ok=True, data=data, evidence=evidence, request_id=request_id)
    except (OSError, RuntimeError, subprocess.TimeoutExpired, ValueError) as exc:
        item = ToolResult(tool=tool, ok=False, error=str(exc), request_id=request_id)
    item.duration_ms = round((time.perf_counter() - started) * 1000)
    log_tool(tool, "ok" if item.ok else "error", item.duration_ms, item.request_id)
    return item


def allowed_subprocess(command: list[str], timeout: int = 15) -> str:
    """Execute only fixed argument lists from an adapter, never user shell text."""
    completed = subprocess.run(
        command,
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
        timeout=timeout,
    )
    return completed.stdout.strip()

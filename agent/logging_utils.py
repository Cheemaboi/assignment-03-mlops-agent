"""Structured logging without configuration values or credentials."""

from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger("mlops_agent")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def log_tool(tool: str, status: str, duration_ms: int, request_id: str, **extra: Any) -> None:
    safe_extra = {k: v for k, v in extra.items() if "token" not in k.lower() and "secret" not in k.lower()}
    logger.info(
        json.dumps(
            {"event": "tool_call", "tool": tool, "status": status, "duration_ms": duration_ms,
             "request_id": request_id, **safe_extra},
            default=str,
        )
    )

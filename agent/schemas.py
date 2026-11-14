"""Shared, deliberately small contracts between tools and the agent."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


@dataclass
class ToolResult:
    tool: str
    ok: bool
    data: dict[str, Any] = field(default_factory=dict)
    evidence: list[str] = field(default_factory=list)
    error: str | None = None
    request_id: str = field(default_factory=lambda: str(uuid4()))
    duration_ms: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AgentResponse:
    answer: str
    request_id: str
    tools_used: list[str]
    evidence: list[str]
    uncertainties: list[str]
    recommended_actions: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


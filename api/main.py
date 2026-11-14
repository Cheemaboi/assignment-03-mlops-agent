"""FastAPI service exposing the MLOps agent."""

from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel, Field

from agent.orchestrator import MLOpsAgent

app = FastAPI(title="Evidence-based MLOps Agent", version="0.1.0")
agent = MLOpsAgent()


class Question(BaseModel):
    message: str = Field(min_length=3, max_length=1000)
    confirmed: bool = False


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/ask")
def ask(payload: Question) -> dict:
    return agent.ask(payload.message, confirmed=payload.confirmed).to_dict()

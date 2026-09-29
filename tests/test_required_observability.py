from __future__ import annotations

import asyncio
from contextlib import contextmanager

import httpx

from app import agent as agent_module
from app.main import app


def test_middleware_accepts_valid_id_and_replaces_invalid_id() -> None:
    async def exercise() -> tuple[httpx.Response, httpx.Response]:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            valid = await client.get("/health", headers={"x-request-id": "req-deadbeef"})
            invalid = await client.get("/health", headers={"x-request-id": "not-safe"})
            return valid, invalid

    valid, invalid = asyncio.run(exercise())
    assert valid.headers["x-request-id"] == "req-deadbeef"
    assert invalid.headers["x-request-id"].startswith("req-")
    assert len(invalid.headers["x-request-id"]) == 12
    assert valid.headers["x-response-time-ms"].isdigit()


class Observation:
    def __init__(self, start: dict) -> None:
        self.start = start
        self.updates: list[dict] = []

    def update(self, **kwargs):
        self.updates.append(kwargs)


class TracingClient:
    def __init__(self) -> None:
        self.observations: list[Observation] = []
        self.span_updates: list[dict] = []

    def get_prompt(self, *args, **kwargs):
        raise TimeoutError("offline")

    def update_current_span(self, **kwargs):
        self.span_updates.append(kwargs)

    @contextmanager
    def start_as_current_observation(self, **kwargs):
        observation = Observation(kwargs)
        self.observations.append(observation)
        yield observation


def test_agent_creates_safe_retrieval_and_generation_children(monkeypatch) -> None:
    client = TracingClient()
    monkeypatch.setattr(agent_module, "get_langfuse_client", lambda: client)
    monkeypatch.setattr(agent_module, "tracing_enabled", lambda: True)

    worker = agent_module.LabAgent()
    agent_module.LabAgent.run.__wrapped__(
        worker,
        user_id="student@example.com",
        feature="monitoring",
        session_id="session@example.com",
        message="Explain monitoring to student@example.com",
        correlation_id="req-12345678",
    )

    assert [item.start["as_type"] for item in client.observations] == [
        "retriever",
        "generation",
    ]
    serialized = repr([(item.start, item.updates) for item in client.observations])
    assert "student@example.com" not in serialized
    generation = client.observations[1]
    assert generation.start["model"] == worker.model
    assert generation.updates[0]["usage_details"]["total"] > 0
    assert generation.updates[0]["cost_details"]["total"] > 0

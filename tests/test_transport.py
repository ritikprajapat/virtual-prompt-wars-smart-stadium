"""Tests for the transport suggestion service and route."""
import pytest

from app.services.transport import suggest_transport
from tests.conftest import FakeLLMClient


async def test_suggest_transport_uses_injected_llm():
    # Proves the DIP seam: an injected LLMClient fully substitutes for Gemini,
    # with no network call and no monkeypatching of the default singleton.
    fake = FakeLLMClient("Take the shuttle from the fake.")
    result = await suggest_transport(5.0, "en", llm=fake)
    assert result == "Take the shuttle from the fake."
    assert "5.0 km" in fake.prompts[0]


async def test_suggest_transport_returns_ai_text(monkeypatch):
    captured = {}

    async def _fake_ask_gemini(prompt: str) -> str:
        captured["prompt"] = prompt
        return "Take the shuttle."

    monkeypatch.setattr("app.services.gemini.ask_gemini", _fake_ask_gemini)
    result = await suggest_transport(5.0, "en")
    assert result == "Take the shuttle."
    assert "5.0 km" in captured["prompt"]


@pytest.mark.parametrize("distance", [0.1, 1.0, 250.0, 500.0])
async def test_suggest_transport_handles_boundary_distances(monkeypatch, distance):
    async def _fake_ask_gemini(prompt: str) -> str:
        return "ok"

    monkeypatch.setattr("app.services.gemini.ask_gemini", _fake_ask_gemini)
    assert await suggest_transport(distance, "fr") == "ok"


async def test_suggest_transport_propagates_runtime_error(monkeypatch):
    async def _boom(prompt: str) -> str:
        raise RuntimeError("AI request failed")

    monkeypatch.setattr("app.services.gemini.ask_gemini", _boom)
    with pytest.raises(RuntimeError):
        await suggest_transport(10.0, "en")


def test_transport_endpoint_returns_suggestion(client, mock_gemini):
    response = client.post(
        "/api/transport/suggest", json={"distance_km": 12, "language": "es"}
    )
    assert response.status_code == 200
    assert response.json() == {"suggestion": "Mocked AI response."}


def test_transport_endpoint_rejects_zero_distance(client, mock_gemini):
    response = client.post("/api/transport/suggest", json={"distance_km": 0})
    assert response.status_code == 422

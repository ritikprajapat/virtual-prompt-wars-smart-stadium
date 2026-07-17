"""Tests for the LLMClient layer: the Gemini/fallback wiring and graceful degrade."""
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.services.llm import (
    FallbackLLMClient,
    GeminiClient,
    LLMClient,
    get_llm_client,
)


class _BoomClient(LLMClient):
    """An LLMClient whose backend is always down (raises like a Gemini outage)."""

    async def generate(self, prompt: str) -> str:
        """Fail exactly as the real client does when the backend is unavailable."""
        raise RuntimeError("backend down")


class _EchoClient(LLMClient):
    """An LLMClient that succeeds, echoing a canned string."""

    async def generate(self, prompt: str) -> str:
        """Return a fixed successful response."""
        return "real phrasing"


async def test_fallback_passes_through_when_inner_succeeds():
    client = FallbackLLMClient(_EchoClient())
    assert await client.generate("prompt") == "real phrasing"


async def test_fallback_returns_static_message_when_inner_fails():
    client = FallbackLLMClient(_BoomClient(), fallback="offline message")
    assert await client.generate("prompt") == "offline message"


def test_get_llm_client_returns_plain_gemini_by_default():
    # Fallback disabled (the default) => failures still surface as a 502.
    assert isinstance(get_llm_client(Settings()), GeminiClient)


def test_get_llm_client_wraps_in_fallback_when_enabled(monkeypatch):
    monkeypatch.setenv("LLM_OFFLINE_FALLBACK", "true")
    assert isinstance(get_llm_client(Settings()), FallbackLLMClient)


def test_get_llm_client_defaults_to_process_settings():
    # No settings passed => resolves the cached process settings.
    assert isinstance(get_llm_client(), LLMClient)


def test_ai_route_degrades_gracefully_when_fallback_enabled(monkeypatch):
    # With the fallback enabled, a Gemini outage no longer 502s: the route
    # returns 200 with a static message in place of AI-generated phrasing.
    monkeypatch.setenv("LLM_OFFLINE_FALLBACK", "true")

    async def _boom(prompt: str) -> str:
        raise RuntimeError("AI request failed")

    monkeypatch.setattr("app.services.gemini.ask_gemini", _boom)

    app = create_app(settings=Settings())
    with TestClient(app) as c:
        response = c.post(
            "/api/transport/suggest", json={"distance_km": 8, "language": "en"}
        )

    assert response.status_code == 200
    assert "temporarily unavailable" in response.json()["suggestion"]

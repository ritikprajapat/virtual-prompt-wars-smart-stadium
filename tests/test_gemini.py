"""Unit tests for the Gemini wrapper itself (not the higher-level services that mock it away)."""
import pytest

from app.services import gemini as gemini_module
from app.services.gemini import ask_gemini


class _FakeResponse:
    def __init__(self, text):
        self.text = text


class _FakeModels:
    def __init__(self, handler):
        self._handler = handler

    def generate_content(self, model, contents):
        return self._handler(model, contents)


class _FakeClient:
    def __init__(self, handler):
        self.models = _FakeModels(handler)


@pytest.fixture(autouse=True)
def _clear_client_cache():
    gemini_module._get_client.cache_clear()
    yield
    gemini_module._get_client.cache_clear()


async def test_ask_gemini_returns_stripped_text(monkeypatch):
    monkeypatch.setattr(
        gemini_module, "_get_client", lambda: _FakeClient(lambda model, contents: _FakeResponse("  Hello, fan!  "))
    )
    assert await ask_gemini("hi") == "Hello, fan!"


async def test_ask_gemini_raises_on_empty_response(monkeypatch):
    monkeypatch.setattr(gemini_module, "_get_client", lambda: _FakeClient(lambda model, contents: _FakeResponse("")))
    with pytest.raises(RuntimeError, match="AI request failed"):
        await ask_gemini("hi")


async def test_ask_gemini_wraps_unexpected_errors(monkeypatch):
    def boom(model, contents):
        raise ValueError("boom")

    monkeypatch.setattr(gemini_module, "_get_client", lambda: _FakeClient(boom))
    with pytest.raises(RuntimeError, match="AI request failed"):
        await ask_gemini("hi")


async def test_ask_gemini_raises_on_timeout(monkeypatch):
    import time

    monkeypatch.setattr(gemini_module, "_TIMEOUT_SECONDS", 0.05)

    def slow(model, contents):
        time.sleep(0.2)
        return _FakeResponse("too late")

    monkeypatch.setattr(gemini_module, "_get_client", lambda: _FakeClient(slow))
    with pytest.raises(RuntimeError, match="AI request timed out"):
        await ask_gemini("hi")


def test_get_client_raises_without_api_key(monkeypatch):
    class _FakeSettings:
        gemini_api_key = ""

    monkeypatch.setattr(gemini_module, "get_settings", lambda: _FakeSettings())
    with pytest.raises(RuntimeError, match="GEMINI_API_KEY is not set"):
        gemini_module._get_client()


def test_get_client_builds_client_when_key_present(monkeypatch):
    class _FakeSettings:
        gemini_api_key = "test-key-123"

    monkeypatch.setattr(gemini_module, "get_settings", lambda: _FakeSettings())
    client = gemini_module._get_client()
    assert client is not None

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.middleware.rate_limiter import limiter
from app.services.crowd import simulator


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    limiter.reset()
    yield
    limiter.reset()


@pytest.fixture(autouse=True)
def _reset_crowd_simulator():
    for gate in simulator.gates.values():
        gate.occupancy = 0
        gate.breached = False
    simulator.alerts = {}
    yield


@pytest.fixture
def mock_gemini(monkeypatch):
    async def _fake_ask_gemini(prompt: str) -> str:
        return "Mocked AI response."

    monkeypatch.setattr("app.services.wayfinding.ask_gemini", _fake_ask_gemini)
    monkeypatch.setattr("app.services.accessibility.ask_gemini", _fake_ask_gemini)
    monkeypatch.setattr("app.services.transport.ask_gemini", _fake_ask_gemini)
    monkeypatch.setattr("app.services.crowd.ask_gemini", _fake_ask_gemini)
    monkeypatch.setattr("app.services.sustainability.ask_gemini", _fake_ask_gemini)
    return _fake_ask_gemini


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

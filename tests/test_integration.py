"""End-to-end wiring: both injected abstractions travelling through app.state.

Builds the app through create_app with an InMemoryVenueRepository and a
FakeLLMClient on app.state — the exact seams create_app already exposes — and
drives a real request to confirm the wiring holds with no file I/O and no
network call.
"""
from fastapi.testclient import TestClient

from app.main import create_app
from app.models.venue import Route
from tests.conftest import FakeLLMClient


def test_wayfinding_route_runs_on_injected_abstractions(in_memory_venue_repository):
    app = create_app(venue_repository=in_memory_venue_repository)
    # app.state is the seam: swap in an offline LLM the same way create_app
    # would have installed the live one.
    app.state.llm = FakeLLMClient("Turn left, then head to your seat.")

    with TestClient(app) as client:
        response = client.post(
            "/api/wayfinding",
            json={
                "start_node_id": "gate_a",
                "target_node_id": "sec_112",
                "language": "en",
            },
        )

    assert response.status_code == 200
    body = response.json()
    Route.model_validate(body["route"])
    # Directions came from the injected FakeLLMClient, not Gemini.
    assert body["directions"] == "Turn left, then head to your seat."
    # The injected repository is the one the app is wired against.
    assert app.state.venue_repository is in_memory_venue_repository

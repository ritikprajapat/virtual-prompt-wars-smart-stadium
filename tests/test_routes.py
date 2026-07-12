"""Integration tests for the API routes: success shapes and 502 error paths."""
import pytest

from app.models.sustainability import SustainabilityResponse
from app.models.venue import Route

# (path, json payload) for each route that phrases text via Gemini and so can 502.
AI_ROUTES = [
    (
        "/api/wayfinding",
        {"start_node_id": "gate_a", "target_node_id": "sec_112", "language": "en"},
    ),
    (
        "/api/accessibility/request",
        {"need_type": "wheelchair", "target_node_id": "sec_210", "language": "en"},
    ),
    ("/api/transport/suggest", {"distance_km": 8, "language": "en"}),
    (
        "/api/sustainability/advise",
        {"start_node_id": "gate_a", "mode": "personal_car", "language": "en"},
    ),
]

# Module path whose `ask_gemini` reference each route ultimately calls.
_SERVICE_MODULE = {
    "/api/wayfinding": "app.services.wayfinding.ask_gemini",
    "/api/accessibility/request": "app.services.accessibility.ask_gemini",
    "/api/transport/suggest": "app.services.transport.ask_gemini",
    "/api/sustainability/advise": "app.services.sustainability.ask_gemini",
}


@pytest.fixture
def failing_gemini(monkeypatch):
    """Patch every service's ask_gemini to raise, simulating a Gemini outage."""

    async def _boom(prompt: str) -> str:
        raise RuntimeError("AI request failed")

    for target in _SERVICE_MODULE.values():
        monkeypatch.setattr(target, _boom)
    return _boom


@pytest.mark.parametrize("path,payload", AI_ROUTES)
def test_ai_route_returns_502_when_gemini_fails(client, failing_gemini, path, payload):
    response = client.post(path, json=payload)
    assert response.status_code == 502
    assert response.json() == {"detail": "AI service unavailable, please try again"}


def test_wayfinding_success_shape_matches_route_model(client, mock_gemini):
    response = client.post(
        "/api/wayfinding",
        json={"start_node_id": "gate_a", "target_node_id": "sec_112", "language": "en"},
    )
    assert response.status_code == 200
    body = response.json()
    # Response route sub-object must validate against the Route model.
    Route.model_validate(body["route"])
    assert isinstance(body["directions"], str)


def test_sustainability_success_shape_matches_response_model(client, mock_gemini):
    response = client.post(
        "/api/sustainability/advise",
        json={"start_node_id": "gate_a", "mode": "walk_bike", "language": "en"},
    )
    assert response.status_code == 200
    model = SustainabilityResponse.model_validate(response.json())
    # walk_bike is the lowest-impact mode: rank 1, nothing lower.
    assert model.comparison.impact_rank == 1
    assert model.comparison.lower_impact_modes == []


def test_accessibility_success_shape(client, mock_gemini):
    response = client.post(
        "/api/accessibility/request",
        json={"need_type": "cognitive", "target_node_id": "sec_210", "language": "de"},
    )
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body["plan"], str)
    assert isinstance(body["facilities"], list)


def test_crowd_simulate_tick_returns_200_shape(client, mock_gemini):
    response = client.post("/api/crowd/simulate-tick")
    assert response.status_code == 200
    body = response.json()
    assert "gates" in body
    assert "new_alerts" in body
    assert isinstance(body["gates"], list)


def test_crowd_status_shape(client):
    response = client.get("/api/crowd/status")
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"gates", "alerts"}
    for gate in body["gates"]:
        assert set(gate) == {
            "gate_id",
            "name",
            "capacity",
            "occupancy",
            "occupancy_pct",
        }

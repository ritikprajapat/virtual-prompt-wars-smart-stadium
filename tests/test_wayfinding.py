import pytest

from app.services.wayfinding import NoRouteFoundError, compute_route


def test_compute_route_finds_shortest_path():
    route = compute_route("gate_a", "sec_112")
    node_ids = [step.node_id for step in route.steps]
    assert node_ids[0] == "gate_a"
    assert node_ids[-1] == "sec_112"
    assert route.total_distance_m > 0
    assert route.total_walk_time_min > 0


def test_compute_route_same_start_and_target():
    route = compute_route("gate_a", "gate_a")
    assert [step.node_id for step in route.steps] == ["gate_a"]
    assert route.total_distance_m == 0
    assert route.total_walk_time_min == 0


def test_compute_route_unknown_node_raises():
    with pytest.raises(NoRouteFoundError):
        compute_route("gate_a", "not_a_real_node")


def test_compute_route_respects_step_free_requirement():
    route = compute_route("gate_a", "sec_325", require_step_free=True)
    assert route.step_free is True


def test_wayfinding_endpoint_returns_ai_phrased_directions(client, mock_gemini):
    response = client.post(
        "/api/wayfinding",
        json={"start_node_id": "gate_a", "target_node_id": "sec_112", "language": "en"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["directions"] == "Mocked AI response."
    assert body["route"]["steps"][0]["node_id"] == "gate_a"


def test_wayfinding_endpoint_unknown_node_returns_404(client, mock_gemini):
    response = client.post(
        "/api/wayfinding",
        json={"start_node_id": "gate_a", "target_node_id": "nowhere", "language": "en"},
    )
    assert response.status_code == 404

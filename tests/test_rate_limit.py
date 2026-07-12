import pytest

from app.config import get_settings

# Every rate-limited POST route with a payload that passes validation.
RATE_LIMITED_ROUTES = [
    (
        "/api/wayfinding",
        {"start_node_id": "gate_a", "target_node_id": "sec_112", "language": "en"},
    ),
    (
        "/api/accessibility/request",
        {"need_type": "wheelchair", "target_node_id": "sec_210", "language": "en"},
    ),
    ("/api/transport/suggest", {"distance_km": 5, "language": "en"}),
    (
        "/api/sustainability/advise",
        {"start_node_id": "gate_a", "mode": "walk_bike", "language": "en"},
    ),
    ("/api/crowd/simulate-tick", None),
]


def test_ai_route_returns_429_past_limit(client, mock_gemini):
    limit = get_settings().rate_limit_per_minute
    payload = {"distance_km": 5, "language": "en"}

    for _ in range(limit):
        response = client.post("/api/transport/suggest", json=payload)
        assert response.status_code == 200

    response = client.post("/api/transport/suggest", json=payload)
    assert response.status_code == 429
    assert "retry-after" in {k.lower() for k in response.headers}


@pytest.mark.parametrize("path,payload", RATE_LIMITED_ROUTES)
def test_every_ai_route_is_rate_limited(client, mock_gemini, path, payload):
    limit = get_settings().rate_limit_per_minute
    kwargs = {"json": payload} if payload is not None else {}

    for _ in range(limit):
        response = client.post(path, **kwargs)
        assert response.status_code == 200

    response = client.post(path, **kwargs)
    assert response.status_code == 429

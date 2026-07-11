from app.config import get_settings


def test_ai_route_returns_429_past_limit(client, mock_gemini):
    limit = get_settings().rate_limit_per_minute
    payload = {"distance_km": 5, "language": "en"}

    for _ in range(limit):
        response = client.post("/api/transport/suggest", json=payload)
        assert response.status_code == 200

    response = client.post("/api/transport/suggest", json=payload)
    assert response.status_code == 429
    assert "retry-after" in {k.lower() for k in response.headers.keys()}

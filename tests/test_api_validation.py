import pytest


@pytest.mark.parametrize(
    "path,payload",
    [
        ("/api/wayfinding", {}),
        ("/api/wayfinding", {"start_node_id": "gate_a"}),
        (
            "/api/wayfinding",
            {"start_node_id": "gate_a", "target_node_id": "sec_112", "language": "xx"},
        ),
        ("/api/accessibility/request", {}),
        (
            "/api/accessibility/request",
            {"need_type": "bogus", "target_node_id": "sec_112"},
        ),
        ("/api/transport/suggest", {"distance_km": -5}),
        ("/api/transport/suggest", {"distance_km": 5000}),
        ("/api/transport/suggest", {}),
    ],
)
def test_invalid_payload_returns_422_not_500(client, mock_gemini, path, payload):
    response = client.post(path, json=payload)
    assert response.status_code == 422


def test_malformed_json_returns_422(client):
    response = client.post(
        "/api/wayfinding",
        content="not json",
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 422

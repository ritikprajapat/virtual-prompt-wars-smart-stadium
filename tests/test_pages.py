def test_index_page_loads(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Multilingual Wayfinding" in response.text


def test_dashboard_page_loads(client):
    response = client.get("/dashboard")
    assert response.status_code == 200
    assert "Live Gate Occupancy" in response.text

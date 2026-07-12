def test_index_page_loads(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Multilingual Wayfinding" in response.text


def test_dashboard_page_loads(client):
    response = client.get("/dashboard")
    assert response.status_code == 200
    assert "Gate Manifest" in response.text


def test_security_headers_present_on_pages(client):
    response = client.get("/")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert "Content-Security-Policy" in response.headers
    assert response.headers["Referrer-Policy"] == "no-referrer"


def test_static_assets_are_served_with_no_cache(client):
    response = client.get("/static/css/style.css")
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-cache"

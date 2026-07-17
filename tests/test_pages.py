from app.main import create_app


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


def test_openapi_schema_exposes_request_examples(client):
    # The request models carry json_schema_extra examples so the generated
    # /docs and /openapi.json are demo-ready.
    schema = client.get("/openapi.json").json()
    wayfinding = schema["components"]["schemas"]["WayFindingRequest"]
    assert wayfinding["example"]["start_node_id"] == "gate_a"


def test_health_endpoint_reports_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_app_uses_injected_simulator():
    # The simulator is now part of the composition root: an explicit instance
    # can be injected instead of the shared module singleton.
    from app.services.crowd import CrowdSimulator, GateState

    sim = CrowdSimulator(
        gates={"x": GateState(gate_id="x", name="Gate X", capacity=10)}
    )
    app = create_app(simulator=sim)
    assert app.state.simulator is sim

"""E2E flow: submit the wayfinding form and see the AI-phrased directions."""
import json

import pytest

pytestmark = pytest.mark.e2e


def test_wayfinding_form_renders_ai_response(page, live_server):
    def _fulfill_wayfinding(route):
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(
                {
                    "route": {
                        "steps": [
                            {
                                "node_id": "gate_a",
                                "node_name": "Gate A - North",
                                "distance_m": 0,
                                "walk_time_min": 0,
                            }
                        ],
                        "total_distance_m": 120,
                        "total_walk_time_min": 3,
                        "step_free": True,
                    },
                    "directions": (
                        "Head straight from Gate A and Section 112 is on your right, "
                        "about a 3 minute walk."
                    ),
                }
            ),
        )

    page.route("**/api/wayfinding", _fulfill_wayfinding)

    page.goto(f"{live_server}/")
    page.select_option("#start_node_id", "gate_a")
    page.select_option("#target_node_id", "sec_112")
    page.click("#wayfinding-form button[type=submit]")

    page.wait_for_selector("#wayfinding-result:not(:empty)")
    assert "3 minute walk" in page.inner_text("#wayfinding-result")
    assert "Route found" in page.inner_text("#wayfinding-status")


def test_dashboard_shows_live_gate_occupancy(page, live_server):
    page.goto(f"{live_server}/dashboard")
    page.wait_for_function(
        "document.querySelector('#occupancy-tbody .occ-value').textContent !== '—'"
    )
    first_row_pct = page.inner_text("#occupancy-tbody .pct-value")
    assert "%" in first_row_pct

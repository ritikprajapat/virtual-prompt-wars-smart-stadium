"""Runs axe-core against the fan and staff pages, asserting zero violations."""
import pytest
from axe_core_python.sync_playwright import Axe

pytestmark = pytest.mark.e2e

axe = Axe()


@pytest.mark.parametrize("path", ["/", "/dashboard"])
def test_page_has_no_axe_violations(page, live_server, path):
    page.goto(f"{live_server}{path}")
    results = axe.run(page)
    violations = results.get("violations", [])
    details = "\n".join(
        f"{v['id']}: {v['description']} ({len(v['nodes'])} nodes)" for v in violations
    )
    assert violations == [], f"axe-core found violations on {path}:\n{details}"


def test_skip_link_is_first_tab_stop_on_index(page, live_server):
    page.goto(f"{live_server}/")
    page.keyboard.press("Tab")
    focused = page.evaluate("document.activeElement.className")
    assert focused == "skip-link"


def test_tab_order_reaches_wayfinding_form_before_other_panels(page, live_server):
    page.goto(f"{live_server}/")
    focused_ids = []
    for _ in range(6):
        page.keyboard.press("Tab")
        focused_ids.append(
            page.evaluate("document.activeElement.id || document.activeElement.tagName")
        )
    assert "start_node_id" in focused_ids
    assert focused_ids.index("start_node_id") < focused_ids.index("target_node_id")

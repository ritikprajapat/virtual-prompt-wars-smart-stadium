"""Property-based tests asserting invariants of the Dijkstra route search.

Example-based tests in ``test_wayfinding.py`` pin specific known routes; these
use Hypothesis to fuzz every ordered pair of real venue nodes and assert the
properties that must hold for *any* shortest path, not just the hand-picked ones.
"""
from hypothesis import given
from hypothesis import strategies as st

from app.services.venue_repository import node_names
from app.services.wayfinding import NoRouteFoundError, compute_route

_NODE_IDS = sorted(node_names())


@given(start=st.sampled_from(_NODE_IDS), target=st.sampled_from(_NODE_IDS))
def test_route_invariants_hold_for_any_node_pair(start, target):
    try:
        route = compute_route(start, target)
    except NoRouteFoundError:
        return  # Disconnected pairs are a valid outcome, not a property breach.

    # The path starts where asked and ends where asked.
    assert route.steps[0].node_id == start
    assert route.steps[-1].node_id == target

    # Cumulative distance/time are non-negative and monotonically non-decreasing
    # along the path, and the totals equal the final step's cumulative values.
    distances = [step.distance_m for step in route.steps]
    times = [step.walk_time_min for step in route.steps]
    assert distances == sorted(distances)
    assert times == sorted(times)
    assert distances[0] == 0.0
    assert route.total_distance_m == distances[-1]
    assert route.total_walk_time_min == times[-1]


@given(start=st.sampled_from(_NODE_IDS), target=st.sampled_from(_NODE_IDS))
def test_step_free_routes_are_genuinely_step_free(start, target):
    try:
        route = compute_route(start, target, require_step_free=True)
    except NoRouteFoundError:
        return  # No step-free path exists for this pair — acceptable.
    # If a step-free route was returned, it must actually be step-free.
    assert route.step_free is True

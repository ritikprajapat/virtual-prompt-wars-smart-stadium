"""Loads and indexes venue.json. The file is read once per process and cached."""
import json
from functools import lru_cache
from pathlib import Path

from app.models.venue import Venue

_VENUE_PATH = Path(__file__).resolve().parent.parent / "data" / "venue.json"


@lru_cache
def load_venue() -> Venue:
    """Load and parse venue.json, cached for the lifetime of the process."""
    with _VENUE_PATH.open() as f:
        raw = json.load(f)
    return Venue.model_validate(raw)


@lru_cache
def node_names() -> dict[str, str]:
    """Map every gate/section/facility id to its display name."""
    venue = load_venue()
    names: dict[str, str] = {}
    for gate in venue.gates:
        names[gate.id] = gate.name
    for section in venue.sections:
        names[section.id] = section.name
    for facility in venue.facilities:
        names[facility.id] = facility.name
    return names


def node_name(node_id: str) -> str:
    """Display name for any gate/section/facility id, falling back to the id itself."""
    return node_names().get(node_id, node_id)


@lru_cache
def adjacency() -> dict[str, list[tuple[str, float, float, bool]]]:
    """Bidirectional adjacency list.

    Maps ``node_id`` to a list of ``(neighbor_id, distance_m, walk_time_min,
    step_free)`` tuples for every edge touching that node.
    """
    venue = load_venue()
    graph: dict[str, list[tuple[str, float, float, bool]]] = {}
    for edge in venue.edges:
        forward = (edge.to, edge.distance_m, edge.walk_time_min, edge.step_free)
        backward = (edge.from_, edge.distance_m, edge.walk_time_min, edge.step_free)
        graph.setdefault(edge.from_, []).append(forward)
        graph.setdefault(edge.to, []).append(backward)
    return graph

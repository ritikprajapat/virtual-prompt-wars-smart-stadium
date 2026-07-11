"""Route computation over the venue graph, plus AI-phrased directions."""
import heapq

from app.models.venue import Route, RouteStep
from app.services.gemini import ask_gemini
from app.services.venue_repository import adjacency, node_names

_LANGUAGE_NAMES = {
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "pt": "Portuguese",
    "ar": "Arabic",
    "de": "German",
    "ja": "Japanese",
    "zh": "Mandarin Chinese",
}


class NoRouteFoundError(Exception):
    pass


def _dijkstra(
    graph: dict[str, list[tuple[str, float, float, bool]]],
    start_node_id: str,
    target_node_id: str,
    require_step_free: bool,
) -> tuple[dict[str, float], dict[str, float], dict[str, bool], dict[str, str]]:
    """Shortest-path search weighted by distance_m, tracking walk time and step-free status alongside."""
    distances: dict[str, float] = {start_node_id: 0.0}
    walk_times: dict[str, float] = {start_node_id: 0.0}
    step_free_so_far: dict[str, bool] = {start_node_id: True}
    previous: dict[str, str] = {}
    visited: set[str] = set()
    queue: list[tuple[float, str]] = [(0.0, start_node_id)]

    while queue:
        dist, node = heapq.heappop(queue)
        if node in visited:
            continue
        visited.add(node)
        if node == target_node_id:
            break
        for neighbor, edge_distance, edge_walk_time, step_free in graph.get(node, []):
            if require_step_free and not step_free:
                continue
            new_dist = dist + edge_distance
            if new_dist < distances.get(neighbor, float("inf")):
                distances[neighbor] = new_dist
                walk_times[neighbor] = walk_times[node] + edge_walk_time
                step_free_so_far[neighbor] = step_free_so_far[node] and step_free
                previous[neighbor] = node
                heapq.heappush(queue, (new_dist, neighbor))

    return distances, walk_times, step_free_so_far, previous


def _reconstruct_path(previous: dict[str, str], start_node_id: str, target_node_id: str) -> list[str]:
    path = [target_node_id]
    while path[-1] != start_node_id:
        path.append(previous[path[-1]])
    path.reverse()
    return path


def compute_route(start_node_id: str, target_node_id: str, require_step_free: bool = False) -> Route:
    """Dijkstra's algorithm over the venue graph, weighted by distance_m.

    Raises NoRouteFoundError if either node is unknown or no path exists
    (e.g. require_step_free excludes the only connecting edges).
    """
    graph = adjacency()
    names = node_names()
    if start_node_id not in graph or target_node_id not in names:
        raise NoRouteFoundError(f"unknown node: {start_node_id} or {target_node_id}")

    distances, walk_times, step_free_so_far, previous = _dijkstra(
        graph, start_node_id, target_node_id, require_step_free
    )

    if target_node_id not in distances:
        raise NoRouteFoundError(f"no route from {start_node_id} to {target_node_id}")

    path = _reconstruct_path(previous, start_node_id, target_node_id)
    steps = [
        RouteStep(
            node_id=node_id,
            node_name=names.get(node_id, node_id),
            distance_m=distances[node_id],
            walk_time_min=walk_times[node_id],
        )
        for node_id in path
    ]

    return Route(
        steps=steps,
        total_distance_m=distances[target_node_id],
        total_walk_time_min=walk_times[target_node_id],
        step_free=step_free_so_far[target_node_id],
    )


async def phrase_directions(route: Route, language: str) -> str:
    """Ask Gemini to turn a computed route into natural, friendly directions."""
    language_name = _LANGUAGE_NAMES.get(language, "English")
    step_names = " -> ".join(step.node_name for step in route.steps)
    prompt = (
        f"You are a stadium wayfinding assistant. Rewrite this route as short, friendly, "
        f"step-by-step walking directions in {language_name}. Keep it under 80 words. "
        f"Mention the total walk time of about {round(route.total_walk_time_min)} minutes.\n\n"
        f"Route waypoints in order: {step_names}."
    )
    return await ask_gemini(prompt)

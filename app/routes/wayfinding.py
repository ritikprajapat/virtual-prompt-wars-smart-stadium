"""HTTP routes for the multilingual wayfinding feature."""
from fastapi import APIRouter, HTTPException, Request, Response

from app.middleware.rate_limiter import ai_rate_limit, limiter
from app.models.requests import WayFindingRequest
from app.routes.errors import ai_service_unavailable
from app.services.wayfinding import NoRouteFoundError, compute_route, phrase_directions

router = APIRouter(prefix="/api/wayfinding", tags=["wayfinding"])


@router.post("")
@limiter.limit(ai_rate_limit)
async def get_wayfinding(
    request: Request, response: Response, payload: WayFindingRequest
) -> dict[str, object]:
    """Compute a route between two nodes and return AI-phrased directions.

    ``response`` is unused here but required by the slowapi rate-limit
    decorator applied above.
    """
    try:
        route = compute_route(
            payload.start_node_id,
            payload.target_node_id,
            require_step_free=payload.require_step_free,
        )
    except NoRouteFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail="No route found between the given locations",
        ) from exc

    try:
        directions = await phrase_directions(
            route, payload.language.value, llm=request.app.state.llm
        )
    except RuntimeError as exc:
        raise ai_service_unavailable() from exc

    return {
        "route": route.model_dump(),
        "directions": directions,
    }

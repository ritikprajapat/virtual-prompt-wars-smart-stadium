"""HTTP routes for the multilingual wayfinding feature."""
from fastapi import APIRouter, HTTPException, Request, Response

from app.middleware.rate_limiter import ai_rate_limit, limiter
from app.models.requests import WayfindingRequest
from app.services.wayfinding import NoRouteFoundError, compute_route, phrase_directions

router = APIRouter(prefix="/api/wayfinding", tags=["wayfinding"])


@router.post("")
@limiter.limit(ai_rate_limit)
async def get_wayfinding(request: Request, response: Response, payload: WayfindingRequest):
    try:
        route = compute_route(
            payload.start_node_id, payload.target_node_id, require_step_free=payload.require_step_free
        )
    except NoRouteFoundError as exc:
        raise HTTPException(status_code=404, detail="No route found between the given locations") from exc

    try:
        directions = await phrase_directions(route, payload.language.value)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail="AI service unavailable, please try again") from exc

    return {
        "route": route.model_dump(),
        "directions": directions,
    }

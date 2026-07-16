"""HTTP routes for the lightweight sustainability/transport panel."""
from fastapi import APIRouter, Request, Response

from app.middleware.rate_limiter import ai_rate_limit, limiter
from app.models.requests import TransportRequest
from app.routes.errors import ai_service_unavailable
from app.services.transport import suggest_transport

router = APIRouter(prefix="/api/transport", tags=["transport"])


@router.post("/suggest")
@limiter.limit(ai_rate_limit)
async def get_transport_suggestion(
    request: Request, response: Response, payload: TransportRequest
) -> dict[str, object]:
    """Return an AI-drafted transit suggestion for the given distance.

    ``response`` is unused here but required by the slowapi rate-limit
    decorator applied above.
    """
    try:
        suggestion = await suggest_transport(
            payload.distance_km, payload.language.value, llm=request.app.state.llm
        )
    except RuntimeError as exc:
        raise ai_service_unavailable() from exc
    return {"suggestion": suggestion}

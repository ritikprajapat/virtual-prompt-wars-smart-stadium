"""HTTP routes for the lightweight sustainability/transport panel."""
from fastapi import APIRouter, HTTPException, Request, Response

from app.middleware.rate_limiter import ai_rate_limit, limiter
from app.models.requests import TransportRequest
from app.services.transport import suggest_transport

router = APIRouter(prefix="/api/transport", tags=["transport"])


@router.post("/suggest")
@limiter.limit(ai_rate_limit)
async def get_transport_suggestion(request: Request, response: Response, payload: TransportRequest):
    try:
        suggestion = await suggest_transport(payload.distance_km, payload.language.value)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail="AI service unavailable, please try again") from exc
    return {"suggestion": suggestion}

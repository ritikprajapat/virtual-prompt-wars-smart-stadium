"""HTTP routes for the Sustainability Advisor feature."""
from fastapi import APIRouter, HTTPException, Request, Response

from app.middleware.rate_limiter import ai_rate_limit, limiter
from app.models.sustainability import SustainabilityRequest
from app.services.sustainability import compare_impact, draft_guidance

router = APIRouter(prefix="/api/sustainability", tags=["sustainability"])


@router.post("/advise")
@limiter.limit(ai_rate_limit)
async def get_sustainability_advice(request: Request, response: Response, payload: SustainabilityRequest):
    comparison = compare_impact(payload.mode)
    try:
        guidance = await draft_guidance(payload.start_node_id, comparison, payload.language.value)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail="AI service unavailable, please try again") from exc

    return {
        "comparison": comparison.model_dump(),
        "guidance": guidance,
    }

"""HTTP routes for the accessibility concierge feature."""
from fastapi import APIRouter, HTTPException, Request, Response

from app.middleware.rate_limiter import ai_rate_limit, limiter
from app.models.requests import AccessibilityRequest
from app.services.accessibility import draft_accommodation_plan, relevant_facilities

router = APIRouter(prefix="/api/accessibility", tags=["accessibility"])


@router.post("/request")
@limiter.limit(ai_rate_limit)
async def request_accommodation(request: Request, response: Response, payload: AccessibilityRequest):
    facilities = relevant_facilities(payload.need_type.value)
    try:
        plan = await draft_accommodation_plan(
            payload.need_type.value, payload.target_node_id, payload.language.value, payload.notes
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail="AI service unavailable, please try again") from exc

    return {
        "plan": plan,
        "facilities": [f.model_dump() for f in facilities],
    }

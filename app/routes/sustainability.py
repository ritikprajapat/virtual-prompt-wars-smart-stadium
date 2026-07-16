"""HTTP routes for the Sustainability Advisor feature."""
from fastapi import APIRouter, Request, Response

from app.middleware.rate_limiter import ai_rate_limit, limiter
from app.models.sustainability import SustainabilityRequest
from app.routes.errors import ai_service_unavailable
from app.services.sustainability import compare_impact, draft_guidance

router = APIRouter(prefix="/api/sustainability", tags=["sustainability"])


@router.post("/advise")
@limiter.limit(ai_rate_limit)
async def get_sustainability_advice(
    request: Request, response: Response, payload: SustainabilityRequest
) -> dict[str, object]:
    """Return an arrival-mode impact comparison plus AI-drafted guidance.

    ``response`` is unused here but required by the slowapi rate-limit
    decorator applied above.
    """
    # pylint: disable=unused-argument
    comparison = compare_impact(payload.mode)
    try:
        guidance = await draft_guidance(
            payload.start_node_id,
            comparison,
            payload.language.value,
            llm=request.app.state.llm,
        )
    except RuntimeError as exc:
        raise ai_service_unavailable() from exc

    return {
        "comparison": comparison.model_dump(),
        "guidance": guidance,
    }

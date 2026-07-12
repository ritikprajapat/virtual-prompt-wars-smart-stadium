"""HTTP routes for live crowd density and staff decision support."""
from dataclasses import asdict

from fastapi import APIRouter, Request, Response

from app.middleware.rate_limiter import ai_rate_limit, limiter
from app.services.crowd import simulator

router = APIRouter(prefix="/api/crowd", tags=["crowd"])


@router.get("/status")
async def crowd_status() -> dict[str, object]:
    """Return the current occupancy snapshot and any active gate alerts."""
    return {
        "gates": simulator.snapshot(),
        "alerts": [asdict(alert) for alert in simulator.active_alerts()],
    }


@router.post("/simulate-tick")
@limiter.limit(ai_rate_limit)
async def simulate_tick(request: Request, response: Response) -> dict[str, object]:
    """Advance the crowd simulation one step and return the new state.

    ``request`` and ``response`` are unused here but required by the slowapi
    rate-limit decorator applied above.
    """
    # pylint: disable=unused-argument
    new_alerts = await simulator.tick()
    return {
        "gates": simulator.snapshot(),
        "new_alerts": [asdict(alert) for alert in new_alerts],
    }

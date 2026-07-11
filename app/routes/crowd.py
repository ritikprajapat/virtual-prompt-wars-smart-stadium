"""HTTP routes for live crowd density and staff decision support."""
from fastapi import APIRouter, Request, Response

from app.middleware.rate_limiter import ai_rate_limit, limiter
from app.services.crowd import simulator

router = APIRouter(prefix="/api/crowd", tags=["crowd"])


@router.get("/status")
async def crowd_status():
    return {
        "gates": simulator.snapshot(),
        "alerts": [a.__dict__ for a in simulator.active_alerts()],
    }


@router.post("/simulate-tick")
@limiter.limit(ai_rate_limit)
async def simulate_tick(request: Request, response: Response):
    new_alerts = await simulator.tick()
    return {
        "gates": simulator.snapshot(),
        "new_alerts": [a.__dict__ for a in new_alerts],
    }

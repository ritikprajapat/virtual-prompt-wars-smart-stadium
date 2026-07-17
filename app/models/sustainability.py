"""Pydantic models for the Sustainability Advisor feature."""
from enum import StrEnum

from pydantic import BaseModel, Field

from app.models.requests import Language


class TransportMode(StrEnum):
    """Arrival modes ranked from lowest to highest relative impact."""

    WALK_BIKE = "walk_bike"
    PUBLIC_TRANSIT = "public_transit"
    RIDESHARE = "rideshare"
    PERSONAL_CAR = "personal_car"


class SustainabilityRequest(BaseModel):
    """Request for sustainability guidance about a planned arrival mode."""

    start_node_id: str = Field(min_length=1, max_length=64)
    mode: TransportMode
    language: Language = Language.EN

    model_config = {
        "json_schema_extra": {
            "example": {
                "start_node_id": "gate_a",
                "mode": "personal_car",
                "language": "en",
            }
        }
    }


class ImpactComparison(BaseModel):
    """A transparent relative-impact ranking — not a real emissions calculation."""

    mode: TransportMode
    impact_rank: int
    lower_impact_modes: list[TransportMode]
    touchpoint: str | None


class SustainabilityResponse(BaseModel):
    """Impact comparison paired with AI-drafted guidance for the guest."""

    comparison: ImpactComparison
    guidance: str

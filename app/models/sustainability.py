"""Pydantic models for the Sustainability Advisor feature."""
from enum import Enum

from pydantic import BaseModel, Field

from app.models.requests import Language


class TransportMode(str, Enum):
    WALK_BIKE = "walk_bike"
    PUBLIC_TRANSIT = "public_transit"
    RIDESHARE = "rideshare"
    PERSONAL_CAR = "personal_car"


class SustainabilityRequest(BaseModel):
    start_node_id: str = Field(min_length=1, max_length=64)
    mode: TransportMode
    language: Language = Language.EN


class ImpactComparison(BaseModel):
    """A simple, transparent relative-impact ranking — not a real emissions calculation."""

    mode: TransportMode
    impact_rank: int
    lower_impact_modes: list[TransportMode]
    touchpoint: str | None


class SustainabilityResponse(BaseModel):
    comparison: ImpactComparison
    guidance: str

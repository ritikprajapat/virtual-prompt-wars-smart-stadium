"""Pydantic models validating inbound API requests."""
from enum import StrEnum

from pydantic import BaseModel, Field


class Language(StrEnum):
    """Supported languages for AI-generated guidance, keyed by ISO 639-1 code."""

    EN = "en"
    ES = "es"
    FR = "fr"
    PT = "pt"
    AR = "ar"
    DE = "de"
    JA = "ja"
    ZH = "zh"


class AccessibilityNeed(StrEnum):
    """Categories of accessibility need a guest can request help for."""

    WHEELCHAIR = "wheelchair"
    HEARING = "hearing"
    VISUAL = "visual"
    COGNITIVE = "cognitive"


class WayFindingRequest(BaseModel):
    """Request to compute and phrase a route between two venue nodes."""

    start_node_id: str = Field(min_length=1, max_length=64)
    target_node_id: str = Field(min_length=1, max_length=64)
    language: Language = Language.EN
    require_step_free: bool = False

    model_config = {
        "json_schema_extra": {
            "example": {
                "start_node_id": "gate_a",
                "target_node_id": "sec_112",
                "language": "en",
                "require_step_free": False,
            }
        }
    }


class AccessibilityRequest(BaseModel):
    """Request for an accessibility accommodation plan to reach a node."""

    need_type: AccessibilityNeed
    target_node_id: str = Field(min_length=1, max_length=64)
    language: Language = Language.EN
    notes: str | None = Field(default=None, max_length=500)

    model_config = {
        "json_schema_extra": {
            "example": {
                "need_type": "wheelchair",
                "target_node_id": "sec_210",
                "language": "en",
                "notes": "Travelling with a service dog.",
            }
        }
    }


class TransportRequest(BaseModel):
    """Request for a transit suggestion given the distance to the venue."""

    distance_km: float = Field(gt=0, le=500)
    language: Language = Language.EN

    model_config = {
        "json_schema_extra": {
            "example": {"distance_km": 8.5, "language": "en"}
        }
    }

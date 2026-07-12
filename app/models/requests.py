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


class WayfindingRequest(BaseModel):
    """Request to compute and phrase a route between two venue nodes."""

    start_node_id: str = Field(min_length=1, max_length=64)
    target_node_id: str = Field(min_length=1, max_length=64)
    language: Language = Language.EN
    require_step_free: bool = False


class AccessibilityRequest(BaseModel):
    """Request for an accessibility accommodation plan to reach a node."""

    need_type: AccessibilityNeed
    target_node_id: str = Field(min_length=1, max_length=64)
    language: Language = Language.EN
    notes: str | None = Field(default=None, max_length=500)


class CrowdQuery(BaseModel):
    """Optional filter selecting a single gate in crowd status queries."""

    gate_id: str | None = Field(default=None, max_length=64)


class TransportRequest(BaseModel):
    """Request for a transit suggestion given the distance to the venue."""

    distance_km: float = Field(gt=0, le=500)
    language: Language = Language.EN

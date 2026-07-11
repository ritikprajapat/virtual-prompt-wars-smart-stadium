"""Pydantic models validating inbound API requests."""
from enum import Enum

from pydantic import BaseModel, Field


class Language(str, Enum):
    EN = "en"
    ES = "es"
    FR = "fr"
    PT = "pt"
    AR = "ar"
    DE = "de"
    JA = "ja"
    ZH = "zh"


class AccessibilityNeed(str, Enum):
    WHEELCHAIR = "wheelchair"
    HEARING = "hearing"
    VISUAL = "visual"
    COGNITIVE = "cognitive"


class WayfindingRequest(BaseModel):
    start_node_id: str = Field(min_length=1, max_length=64)
    target_node_id: str = Field(min_length=1, max_length=64)
    language: Language = Language.EN
    require_step_free: bool = False


class AccessibilityRequest(BaseModel):
    need_type: AccessibilityNeed
    target_node_id: str = Field(min_length=1, max_length=64)
    language: Language = Language.EN
    notes: str | None = Field(default=None, max_length=500)


class CrowdQuery(BaseModel):
    gate_id: str | None = Field(default=None, max_length=64)


class TransportRequest(BaseModel):
    distance_km: float = Field(gt=0, le=500)
    language: Language = Language.EN

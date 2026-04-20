from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class Verdict(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    label: str
    severity: str
    authenticity_score: int = Field(ge=0, le=100)
    model_confidence: float = Field(ge=0.0, le=1.0)
    model_label: str


class ArtifactIndicator(BaseModel):
    type: str
    severity: str  # low | medium | high
    description: str
    confidence: float = Field(ge=0.0, le=1.0)


class TrustedSource(BaseModel):
    source_name: str
    title: str
    url: str
    published_at: Optional[str] = None
    relevance_score: float = Field(ge=0.0, le=1.0)


class ContradictingEvidence(BaseModel):
    source_name: str
    title: str
    url: str
    type: str = "fact_check"


class TruthOverride(BaseModel):
    applied: bool = False
    source_url: str = ""
    source_name: str = ""
    similarity: float = 0.0
    fake_prob_before: float = 0.0
    fake_prob_after: float = 0.0


class ExifSummary(BaseModel):
    make: Optional[str] = None
    model: Optional[str] = None
    datetime_original: Optional[str] = None
    gps_info: Optional[str] = None
    software: Optional[str] = None
    lens_model: Optional[str] = None
    trust_adjustment: int = 0  # negative = more real, positive = more fake
    trust_reason: str = ""


class LLMExplainabilitySummary(BaseModel):
    paragraph: str = ""
    bullets: List[str] = []
    model_used: str = ""
    cached: bool = False


class VLMComponentScore(BaseModel):
    score: int = Field(ge=0, le=100, default=75)
    notes: str = ""


class VLMBreakdown(BaseModel):
    facial_symmetry: VLMComponentScore = VLMComponentScore()
    skin_texture: VLMComponentScore = VLMComponentScore()
    lighting_consistency: VLMComponentScore = VLMComponentScore()
    background_coherence: VLMComponentScore = VLMComponentScore()
    anatomy_hands_eyes: VLMComponentScore = VLMComponentScore()
    context_objects: VLMComponentScore = VLMComponentScore()
    model_used: str = ""
    cached: bool = False


class ProcessingSummary(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    stages_completed: List[str]
    total_duration_ms: int
    model_used: str
    models_used: List[str] = []  # all models that contributed (ensemble)

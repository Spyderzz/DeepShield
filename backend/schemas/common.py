from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

ANALYSIS_CACHE_VERSION = "2026-05-06-phase-a-unified-fusion"


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
    description: Optional[str] = None
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
    icc_profile: Optional[bool] = False
    maker_note: Optional[bool] = False
    trust_adjustment: int = 0  # negative = more real, positive = more fake
    trust_reason: str = ""


class SignalObservation(BaseModel):
    """One forensic signal with a plain-English observation. Used in image analysis."""
    name: str
    observation: str
    verdict: str = ""  # "authentic" | "suspicious" | "inconclusive"


class LLMExplainabilitySummary(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    paragraph: str = ""
    bullets: List[str] = []
    # Per-signal breakdown for image analysis (empty for non-image media)
    signals: List[SignalObservation] = []
    model_used: str = ""
    cached: bool = False


class VLMComponentScore(BaseModel):
    score: int = Field(ge=0, le=100, default=75)
    notes: str = ""


class VLMBreakdown(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

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
    analysis_version: str = ANALYSIS_CACHE_VERSION
    calibrator_applied: bool = False
    # Phase A/B: unified evidence fusion details and disagreement clamping
    evidence_fusion: Optional[dict] = None
    disagreement_reason: Optional[str] = None
    gating_applied: Optional[str] = None

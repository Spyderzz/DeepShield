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


class ProcessingSummary(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    stages_completed: List[str]
    total_duration_ms: int
    model_used: str

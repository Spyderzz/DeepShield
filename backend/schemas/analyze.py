from __future__ import annotations

from typing import List

from pydantic import BaseModel

from schemas.common import (
    ArtifactIndicator,
    ContradictingEvidence,
    ProcessingSummary,
    TrustedSource,
    Verdict,
)


class ImageExplainability(BaseModel):
    heatmap_base64: str = ""
    artifact_indicators: List[ArtifactIndicator] = []


class ImageAnalysisResponse(BaseModel):
    analysis_id: str
    media_type: str = "image"
    timestamp: str
    verdict: Verdict
    explainability: ImageExplainability
    trusted_sources: List[TrustedSource] = []
    contradicting_evidence: List[ContradictingEvidence] = []
    processing_summary: ProcessingSummary
    responsible_ai_notice: str = (
        "AI-based analysis may not be 100% accurate. Cross-check with trusted sources before sharing."
    )

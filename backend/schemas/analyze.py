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


class TextExplainability(BaseModel):
    fake_probability: float
    top_label: str
    all_scores: dict = {}
    keywords: List[str] = []


class TextAnalysisResponse(BaseModel):
    analysis_id: str
    media_type: str = "text"
    timestamp: str
    verdict: Verdict
    explainability: TextExplainability
    trusted_sources: List[TrustedSource] = []
    contradicting_evidence: List[ContradictingEvidence] = []
    processing_summary: ProcessingSummary
    responsible_ai_notice: str = (
        "AI-based analysis may not be 100% accurate. Cross-check with trusted sources before sharing."
    )


class ImageExplainability(BaseModel):
    heatmap_base64: str = ""
    artifact_indicators: List[ArtifactIndicator] = []


class FrameAnalysisOut(BaseModel):
    index: int
    timestamp_s: float
    label: str
    confidence: float
    suspicious_prob: float
    is_suspicious: bool
    has_face: bool = False
    scored: bool = False


class VideoExplainability(BaseModel):
    num_frames_sampled: int
    num_face_frames: int = 0
    num_suspicious_frames: int
    mean_suspicious_prob: float
    max_suspicious_prob: float
    suspicious_ratio: float
    insufficient_faces: bool = False
    suspicious_timestamps: List[float] = []
    frames: List[FrameAnalysisOut] = []


class VideoAnalysisResponse(BaseModel):
    analysis_id: str
    media_type: str = "video"
    timestamp: str
    verdict: Verdict
    explainability: VideoExplainability
    trusted_sources: List[TrustedSource] = []
    contradicting_evidence: List[ContradictingEvidence] = []
    processing_summary: ProcessingSummary
    responsible_ai_notice: str = (
        "AI-based analysis may not be 100% accurate. Cross-check with trusted sources before sharing."
    )


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

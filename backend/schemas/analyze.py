from __future__ import annotations

from typing import List

from pydantic import BaseModel

from schemas.common import (
    ArtifactIndicator,
    ContradictingEvidence,
    ExifSummary,
    LLMExplainabilitySummary,
    ProcessingSummary,
    TrustedSource,
    TruthOverride,
    Verdict,
    VLMBreakdown,
)


class SensationalismBreakdown(BaseModel):
    score: int = 0
    level: str = "Low"
    exclamation_count: int = 0
    caps_word_count: int = 0
    clickbait_matches: int = 0
    emotional_word_count: int = 0
    superlative_count: int = 0


class ManipulationIndicatorOut(BaseModel):
    pattern_type: str
    matched_text: str
    start_pos: int
    end_pos: int
    severity: str
    description: str


class TextExplainability(BaseModel):
    fake_probability: float
    top_label: str
    all_scores: dict = {}
    keywords: List[str] = []
    sensationalism: SensationalismBreakdown = SensationalismBreakdown()
    manipulation_indicators: List[ManipulationIndicatorOut] = []
    detected_language: str = "en"       # ISO 639-1 code, e.g. "en", "hi"
    truth_override: TruthOverride | None = None


class TextAnalysisResponse(BaseModel):
    analysis_id: str
    record_id: int = 0
    media_type: str = "text"
    timestamp: str
    verdict: Verdict
    explainability: TextExplainability
    llm_summary: LLMExplainabilitySummary | None = None
    trusted_sources: List[TrustedSource] = []
    contradicting_evidence: List[ContradictingEvidence] = []
    processing_summary: ProcessingSummary
    responsible_ai_notice: str = (
        "AI-based analysis may not be 100% accurate. Cross-check with trusted sources before sharing."
    )


class OCRBoxOut(BaseModel):
    text: str
    bbox: List[List[int]]
    confidence: float


class SuspiciousPhraseOut(BaseModel):
    text: str
    bbox: List[List[int]]
    pattern_type: str
    severity: str
    description: str


class LayoutAnomalyOut(BaseModel):
    type: str
    severity: str
    description: str
    confidence: float


class ScreenshotExplainability(BaseModel):
    extracted_text: str = ""
    ocr_boxes: List[OCRBoxOut] = []
    fake_probability: float = 0.0
    sensationalism: SensationalismBreakdown = SensationalismBreakdown()
    suspicious_phrases: List[SuspiciousPhraseOut] = []
    layout_anomalies: List[LayoutAnomalyOut] = []
    keywords: List[str] = []
    detected_language: str = "en"
    truth_override: TruthOverride | None = None


class ScreenshotAnalysisResponse(BaseModel):
    analysis_id: str
    record_id: int = 0
    media_type: str = "screenshot"
    timestamp: str
    verdict: Verdict
    explainability: ScreenshotExplainability
    llm_summary: LLMExplainabilitySummary | None = None
    trusted_sources: List[TrustedSource] = []
    contradicting_evidence: List[ContradictingEvidence] = []
    processing_summary: ProcessingSummary
    responsible_ai_notice: str = (
        "AI-based analysis may not be 100% accurate. Cross-check with trusted sources before sharing."
    )


class ImageExplainability(BaseModel):
    heatmap_base64: str = ""
    ela_base64: str = ""
    boxes_base64: str = ""
    heatmap_status: str = "success"  # success | failed | degraded
    artifact_indicators: List[ArtifactIndicator] = []
    exif: ExifSummary | None = None
    llm_summary: LLMExplainabilitySummary | None = None
    vlm_breakdown: VLMBreakdown | None = None


class FrameAnalysisOut(BaseModel):
    index: int
    timestamp_s: float
    label: str
    confidence: float
    suspicious_prob: float
    is_suspicious: bool
    has_face: bool = False
    scored: bool = False


class AudioExplainability(BaseModel):
    audio_authenticity_score: float = 100.0
    has_audio: bool = False
    duration_s: float = 0.0
    silence_ratio: float = 0.0
    spectral_variance: float = 0.0
    rms_consistency: float = 0.0
    notes: str = ""


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
    # Phase 17.1 — temporal consistency
    temporal_score: float | None = None
    optical_flow_variance: float | None = None
    flicker_score: float | None = None
    blink_rate_anomaly: bool | None = None
    # Phase 17.2 — audio deepfake detection
    audio: AudioExplainability | None = None


class VideoAnalysisResponse(BaseModel):
    analysis_id: str
    record_id: int = 0
    media_type: str = "video"
    timestamp: str
    verdict: Verdict
    explainability: VideoExplainability
    llm_summary: LLMExplainabilitySummary | None = None
    trusted_sources: List[TrustedSource] = []
    contradicting_evidence: List[ContradictingEvidence] = []
    processing_summary: ProcessingSummary
    responsible_ai_notice: str = (
        "AI-based analysis may not be 100% accurate. Cross-check with trusted sources before sharing."
    )


class ImageAnalysisResponse(BaseModel):
    analysis_id: str
    record_id: int = 0
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

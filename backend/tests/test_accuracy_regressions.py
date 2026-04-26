from __future__ import annotations

import os

os.environ["DEBUG"] = "false"

from schemas.common import TrustedSource
from services.news_lookup import _compute_truth_override
from services.screenshot_service import OCRBox, extract_full_text
from services.text_service import _scores_to_classification
from utils.scoring import compute_video_authenticity_score
from schemas.common import ArtifactIndicator, ExifSummary, VLMComponentScore, VLMBreakdown
from services.general_image_service import GeneralImageDetection, fuse_no_face_evidence


def test_video_score_uses_temporal_and_audio_when_face_content_is_insufficient():
    score, label, severity = compute_video_authenticity_score(
        mean_suspicious_prob=0.0,
        insufficient_faces=True,
        temporal_score=20.0,
        audio_authenticity_score=10.0,
        has_audio=True,
    )

    assert score < 35
    assert label != "Insufficient face content"
    assert severity in {"critical", "danger"}


def test_text_classifier_treats_unknown_label_mapping_as_uncertain():
    clf = _scores_to_classification(
        [
            {"label": "LABEL_0", "score": 0.99},
            {"label": "LABEL_1", "score": 0.01},
        ],
        allow_label0_fallback=False,
    )

    assert clf.fake_prob == 0.5
    assert clf.label == "uncertain_label_mapping"


def test_ocr_text_extraction_filters_low_confidence_noise():
    boxes = [
        OCRBox(text="BREAKING", bbox=[[0, 0], [1, 0], [1, 1], [0, 1]], confidence=0.92),
        OCRBox(text="x7q", bbox=[[0, 2], [1, 2], [1, 3], [0, 3]], confidence=0.08),
        OCRBox(text="confirmed report", bbox=[[0, 4], [1, 4], [1, 5], [0, 5]], confidence=0.51),
    ]

    assert extract_full_text(boxes) == "BREAKING confirmed report"


def test_truth_override_does_not_apply_from_headline_only_match(monkeypatch):
    class FakeSentenceTransformer:
        def encode(self, texts, convert_to_numpy=True, normalize_embeddings=True):
            import numpy as np

            return np.array([[1.0, 0.0], [1.0, 0.0]], dtype=float)

    class FakeLoader:
        def load_sentence_transformer(self):
            return FakeSentenceTransformer()

    monkeypatch.setattr("models.model_loader.get_model_loader", lambda: FakeLoader())

    override = _compute_truth_override(
        "Prime Minister announces vaccine drive across Delhi hospitals",
        [
            TrustedSource(
                source_name="Reuters",
                title="Prime Minister announces vaccine drive",
                url="https://www.reuters.com/world/example",
                relevance_score=1.0,
            )
        ],
        current_fake_prob=0.9,
    )

    assert override is None or not override.applied


def test_no_face_fusion_uses_general_detector_forensic_and_exif_evidence():
    fused = fuse_no_face_evidence(
        general_fake_prob=0.72,
        artifacts=[
            ArtifactIndicator(
                type="gan_artifact",
                severity="high",
                description="elevated frequency artifacts",
                confidence=0.80,
            ),
            ArtifactIndicator(
                type="compression",
                severity="medium",
                description="unusual compression",
                confidence=0.55,
            ),
        ],
        exif=ExifSummary(software="Stable Diffusion", trust_adjustment=10),
    )

    assert fused.fake_probability > 0.72
    assert fused.method == "no_face_general_forensic_fusion"
    assert fused.components["general_detector"] == 0.72
    assert fused.components["forensics"] > 0.5
    assert fused.components["exif"] > 0.5


def test_no_face_fusion_can_use_vlm_consistency_scores():
    fused = fuse_no_face_evidence(
        general_fake_prob=0.40,
        artifacts=[],
        exif=None,
        vlm=VLMBreakdown(
            facial_symmetry=VLMComponentScore(score=80),
            skin_texture=VLMComponentScore(score=80),
            lighting_consistency=VLMComponentScore(score=25),
            background_coherence=VLMComponentScore(score=20),
            anatomy_hands_eyes=VLMComponentScore(score=35),
            context_objects=VLMComponentScore(score=30),
        ),
    )

    assert fused.fake_probability > 0.40
    assert fused.components["vlm_consistency"] > 0.5


def test_no_face_image_route_skips_face_trained_classifiers(monkeypatch):
    from PIL import Image
    import services.image_service as image_service

    monkeypatch.setattr(image_service, "_has_face_for_routing", lambda _img: False)
    monkeypatch.setattr(
        image_service,
        "classify_general_image",
        lambda _img: GeneralImageDetection(
            fake_probability=0.8,
            label="generated",
            all_scores={"generated": 0.8, "real": 0.2},
            model_used="test-general-detector",
        ),
    )
    monkeypatch.setattr(
        image_service,
        "_classify_vit",
        lambda _img: (_ for _ in ()).throw(AssertionError("face-centric ViT should not run")),
    )
    monkeypatch.setattr(
        image_service,
        "_classify_ffpp",
        lambda _img: (_ for _ in ()).throw(AssertionError("FFPP should not run")),
    )

    result = image_service.classify_image(Image.new("RGB", (32, 32), "white"))

    assert result.ensemble_method == "no_face_general_forensic_fusion"
    assert result.models_used == ["test-general-detector"]
    assert result.no_face_analysis is not None

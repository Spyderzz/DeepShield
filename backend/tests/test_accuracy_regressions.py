from __future__ import annotations

import os
import asyncio

os.environ["DEBUG"] = "false"

from schemas.common import TrustedSource
from services.news_lookup import _compute_truth_override, search_news_full
from services.screenshot_service import OCRBox, extract_full_text
from services.text_service import _scores_to_classification
from utils.scoring import apply_unverified_news_gate, compute_video_authenticity_score
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


def test_unverified_news_gate_caps_real_scores_as_suspicious():
    score, label, severity, reason = apply_unverified_news_gate(
        92,
        has_trusted_sources=False,
        has_contradicting_evidence=False,
        truth_override_applied=False,
    )

    assert score == 55
    assert label == "Suspicious"
    assert severity == "warning"
    assert reason == "no_trusted_source"


def test_unverified_news_gate_keeps_fake_scores_fake():
    score, label, severity, reason = apply_unverified_news_gate(
        18,
        has_trusted_sources=False,
        has_contradicting_evidence=False,
        truth_override_applied=False,
    )

    assert score == 18
    assert label == "Very Likely Fake"
    assert severity == "critical"
    assert reason == "no_trusted_source"


def test_news_lookup_falls_back_from_recent_india_to_older_india(monkeypatch):
    calls = []

    async def fake_fetch(params):
        calls.append(dict(params))
        if params.get("country") == "in" and params.get("_endpoint") == "archive":
            return [
                {
                    "link": "https://indianexpress.com/article/cities/kolkata/example",
                    "title": "BJP leader aide shot dead in Bengal",
                    "source_id": "indianexpress",
                    "pubDate": "2026-05-07 00:43:00",
                    "description": "Police launched an investigation.",
                }
            ]
        return []

    monkeypatch.setattr("services.news_lookup.settings.NEWS_API_KEY", "test-key")
    monkeypatch.setattr("services.news_lookup._fetch", fake_fetch)
    monkeypatch.setattr("services.news_lookup._compute_truth_override", lambda *args, **kwargs: None)

    result = asyncio.run(
        search_news_full(
            ["BJP", "Suvendu", "Adhikari", "Madhyamgram"],
            original_text="BJP leader Suvendu Adhikari's PA shot dead in West Bengal's Madhyamgram",
        )
    )

    assert result.trusted_sources[0].source_name == "indianexpress"
    assert calls[0]["country"] == "in"
    assert calls[0]["timeframe"] == "1"
    archive_call = next(call for call in calls if call.get("country") == "in" and call.get("_endpoint") == "archive")
    assert archive_call["_url"].endswith("/archive")
    assert "timeframe" not in archive_call
    assert "from_date" in archive_call
    assert "to_date" in archive_call


def test_news_lookup_falls_back_to_global_when_india_has_no_results(monkeypatch):
    calls = []

    async def fake_fetch(params):
        calls.append(dict(params))
        if "country" not in params and params.get("timeframe") == "1":
            return [
                {
                    "link": "https://www.reuters.com/world/example",
                    "title": "US and EU announce new trade framework",
                    "source_id": "reuters",
                    "pubDate": "2026-05-07 01:05:00",
                    "description": "Officials announced a new framework.",
                }
            ]
        return []

    monkeypatch.setattr("services.news_lookup.settings.NEWS_API_KEY", "test-key")
    monkeypatch.setattr("services.news_lookup._fetch", fake_fetch)
    monkeypatch.setattr("services.news_lookup._compute_truth_override", lambda *args, **kwargs: None)

    result = asyncio.run(
        search_news_full(
            ["US", "EU", "trade", "framework"],
            original_text="US and EU announce new trade framework",
        )
    )

    assert result.trusted_sources[0].source_name == "reuters"
    assert any(call.get("country") == "in" for call in calls)
    assert any("country" not in call for call in calls)


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


def test_synthetic_still_override_keeps_strong_ai_detector_authoritative():
    import services.image_service as image_service

    adjusted, reason = image_service._apply_synthetic_still_overrides(
        fake_prob=0.13,
        general_fake_prob=0.93,
        is_video_frame=False,
    )

    assert adjusted >= 0.90
    assert reason == "general_detector_very_high(0.93)"


def test_synthetic_still_override_does_not_affect_video_frame_route():
    import services.image_service as image_service

    adjusted, reason = image_service._apply_synthetic_still_overrides(
        fake_prob=0.13,
        general_fake_prob=0.93,
        is_video_frame=True,
    )

    assert adjusted == 0.13
    assert reason is None


def test_heatmap_target_index_prefers_fake_label_tokens():
    from types import SimpleNamespace

    from models.heatmap_generator import _find_class_index

    model = SimpleNamespace(config=SimpleNamespace(id2label={0: "real", 1: "fake"}))

    assert _find_class_index(model, ("fake", "generated", "synthetic")) == 1


def test_video_efficientnet_frame_scored_is_boolean(monkeypatch):
    import numpy as np
    from PIL import Image

    import services.video_service as video_service

    class FakeEfficientNet:
        calibrator_applied = False

        class FaceExtractor:
            def process_image(self, img):
                return {"faces": [np.zeros((16, 16, 3), dtype=np.uint8)]}

        face_extractor = FaceExtractor()

        def _fallback_face_crop(self, img):
            return None

    class FakeLoader:
        def load_efficientnet(self):
            return FakeEfficientNet()

    monkeypatch.setattr(video_service, "get_model_loader", lambda: FakeLoader())
    monkeypatch.setattr(video_service, "_score_efficientnet_face", lambda _eff, _face: 0.7)

    frame = np.zeros((32, 32, 3), dtype=np.uint8)
    results, *_ = video_service._analyze_with_efficientnet(
        [(0, 0.0, frame, Image.fromarray(frame))]
    )

    assert results[0].scored is True
    assert isinstance(results[0].scored, bool)


def test_video_primary_path_weights_ffpp_vit_above_efficientnet(monkeypatch):
    import numpy as np
    from PIL import Image

    import services.video_service as video_service

    class FakeEfficientNet:
        calibrator_applied = False

        class FaceExtractor:
            def process_image(self, img):
                return {"faces": [np.zeros((16, 16, 3), dtype=np.uint8)]}

        face_extractor = FaceExtractor()

        def _fallback_face_crop(self, img):
            return None

    class FakeLoader:
        def load_efficientnet(self):
            return FakeEfficientNet()

    monkeypatch.setattr(video_service, "get_model_loader", lambda: FakeLoader())
    monkeypatch.setattr(video_service, "_score_efficientnet_face", lambda _eff, _face: 0.10)
    monkeypatch.setattr(video_service, "_classify_ffpp", lambda _pil: (0.90, {"fake": 0.90, "real": 0.10}))

    frame = np.zeros((32, 32, 3), dtype=np.uint8)
    results, _detector, models_used, _calibrated = video_service._analyze_with_efficientnet(
        [(0, 0.0, frame, Image.fromarray(frame))]
    )

    assert results[0].suspicious_prob > 0.60
    assert results[0].label == "Fake"
    assert "ffpp-vit-local" in models_used

from __future__ import annotations

from pathlib import Path
from threading import Lock
from typing import Optional, Tuple

from loguru import logger

from config import settings


class ModelLoader:
    """Singleton holder for preloaded AI models. Thread-safe lazy init."""

    _instance: Optional["ModelLoader"] = None
    _lock: Lock = Lock()

    def __new__(cls) -> "ModelLoader":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._image_model = None
                    cls._instance._image_processor = None
                    cls._instance._general_image_model = None
                    cls._instance._general_image_processor = None
                    cls._instance._general_image_unavailable = False
                    cls._instance._text_pipeline = None
                    cls._instance._multilang_text_pipeline = None
                    cls._instance._ocr_reader = None
                    cls._instance._face_detector = None
                    cls._instance._face_detector_unavailable = False
                    cls._instance._spacy_nlp = None
                    cls._instance._sentence_transformer = None
                    cls._instance._efficientnet_detector = None
                    cls._instance._ffpp_model = None
                    cls._instance._ffpp_processor = None
        return cls._instance

    @classmethod
    def get_instance(cls) -> "ModelLoader":
        return cls()

    # ---------- Image (ViT deepfake classifier) ----------
    def load_image_model(self) -> Tuple[object, object]:
        if self._image_model is None:
            logger.info(f"Loading image model: {settings.IMAGE_MODEL_ID}")
            from transformers import AutoImageProcessor, AutoModelForImageClassification

            self._image_processor = AutoImageProcessor.from_pretrained(settings.IMAGE_MODEL_ID)
            model = AutoModelForImageClassification.from_pretrained(settings.IMAGE_MODEL_ID)
            model.to(settings.DEVICE)
            model.eval()
            self._image_model = model
            logger.info("Image model loaded")
        return self._image_model, self._image_processor

    # ---------- General AI image detector (no-face scenes / objects / art) ----------
    def load_general_image_model(self) -> Optional[Tuple[object, object]]:
        if self._general_image_unavailable:
            return None
        if self._general_image_model is None:
            try:
                logger.info(f"Loading general AI image model: {settings.GENERAL_IMAGE_MODEL_ID}")
                from transformers import AutoImageProcessor, AutoModelForImageClassification

                self._general_image_processor = AutoImageProcessor.from_pretrained(settings.GENERAL_IMAGE_MODEL_ID)
                model = AutoModelForImageClassification.from_pretrained(settings.GENERAL_IMAGE_MODEL_ID)
                model.to(settings.DEVICE)
                model.eval()
                self._general_image_model = model
                logger.info("General AI image model loaded")
            except Exception as e:  # noqa: BLE001
                self._general_image_unavailable = True
                logger.warning(f"General AI image model load failed: {e}")
                return None
        return self._general_image_model, self._general_image_processor

    # ---------- Text (BERT fake-news classifier — English) ----------
    def load_text_model(self):
        if self._text_pipeline is None:
            logger.info(f"Loading text model: {settings.TEXT_MODEL_ID}")
            from transformers import pipeline

            self._text_pipeline = pipeline(
                "text-classification",
                model=settings.TEXT_MODEL_ID,
                device=0 if settings.DEVICE == "cuda" else -1,
            )
            logger.info("Text model loaded")
        return self._text_pipeline

    # ---------- Multilingual text model (Phase 13) ----------
    def load_multilang_text_model(self):
        """Load multilingual fake-news classifier. Falls back to English model if not configured."""
        model_id = settings.TEXT_MULTILANG_MODEL_ID
        if not model_id:
            logger.debug("TEXT_MULTILANG_MODEL_ID not set — falling back to English text model")
            return self.load_text_model()

        if self._multilang_text_pipeline is None:
            logger.info(f"Loading multilingual text model: {model_id}")
            from transformers import pipeline

            self._multilang_text_pipeline = pipeline(
                "text-classification",
                model=model_id,
                device=0 if settings.DEVICE == "cuda" else -1,
            )
            logger.info("Multilingual text model loaded")
        return self._multilang_text_pipeline

    # ---------- spaCy NLP (Phase 13 NER) ----------
    def load_spacy_nlp(self):
        """Lazy-load spaCy English NLP model. Returns None if spaCy is not installed."""
        if self._spacy_nlp is None:
            try:
                import spacy  # type: ignore
                try:
                    self._spacy_nlp = spacy.load("en_core_web_sm")
                    logger.info("spaCy en_core_web_sm loaded")
                except OSError:
                    logger.warning(
                        "spaCy model 'en_core_web_sm' not found. "
                        "Run: python -m spacy download en_core_web_sm"
                    )
                    return None
            except ImportError:
                logger.warning("spaCy not installed — NER keyword extraction disabled")
                return None
        return self._spacy_nlp

    # ---------- Sentence-Transformer (Phase 13 truth-override) ----------
    def load_sentence_transformer(self):
        """Lazy-load sentence-transformers/all-MiniLM-L6-v2. Returns None if not installed."""
        if self._sentence_transformer is None:
            try:
                from sentence_transformers import SentenceTransformer  # type: ignore
                self._sentence_transformer = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
                logger.info("Sentence-transformer (all-MiniLM-L6-v2) loaded")
            except ImportError:
                logger.warning("sentence-transformers not installed — truth-override disabled")
                return None
            except Exception as e:
                logger.warning(f"Sentence-transformer load failed: {e}")
                return None
        return self._sentence_transformer

    # ---------- OCR (EasyOCR) — Phase 13: use OCR_LANGS from config ----------
    def load_ocr_engine(self):
        if self._ocr_reader is None:
            langs = [l.strip() for l in settings.OCR_LANGS.split(",") if l.strip()]
            if not langs:
                langs = ["en"]
            logger.info(f"Loading EasyOCR reader (langs: {langs})")
            import easyocr  # type: ignore

            self._ocr_reader = easyocr.Reader(
                langs, gpu=(settings.DEVICE == "cuda"), verbose=False, download_enabled=True,
            )
            logger.info("EasyOCR loaded")
        return self._ocr_reader

    # ---------- Face detector (MediaPipe) ----------
    def load_face_detector(self):
        if self._face_detector_unavailable:
            return None
        if self._face_detector is None:
            logger.info("Loading MediaPipe FaceMesh")
            try:
                import mediapipe as mp  # type: ignore

                if not hasattr(mp, "solutions"):
                    raise ImportError("installed mediapipe package has no solutions API")

                self._face_detector = mp.solutions.face_mesh.FaceMesh(
                    static_image_mode=True,
                    max_num_faces=5,
                    min_detection_confidence=0.5,
                )
            except Exception as exc:  # noqa: BLE001
                self._face_detector_unavailable = True
                logger.warning(f"MediaPipe FaceMesh unavailable: {exc}")
                return None
            logger.info("MediaPipe FaceMesh loaded")
        return self._face_detector

    # ---------- EfficientNetAutoAttB4 (ICPR2020 / DeepShield1 merge) ----------
    def load_efficientnet(self):
        """Lazy-load EfficientNetAutoAttB4 detector. Returns None if deps are missing."""
        if self._efficientnet_detector is None:
            try:
                from services.efficientnet_service import EfficientNetDetector

                self._efficientnet_detector = EfficientNetDetector(
                    model_name=settings.EFFICIENTNET_MODEL,
                    train_db=settings.EFFICIENTNET_TRAIN_DB,
                    device=settings.DEVICE,
                )
            except Exception as e:
                logger.warning(f"EfficientNet load failed (continuing without it): {e}")
                return None
        return self._efficientnet_detector

    # ---------- FFPP-fine-tuned ViT (Phase 11.3) ----------
    def load_ffpp_model(self) -> Optional[Tuple[object, object]]:
        """Lazy-load the FaceForensics++ fine-tuned ViT from a local checkpoint.

        The checkpoint directory was exported from Colab with only
        `model.safetensors` + `config.json` (no preprocessor_config.json), so the
        image processor is loaded from the base google/vit-base-patch16-224-in21k
        — this matches the processor used during training.

        Returns None if disabled or the checkpoint is missing.
        """
        if not settings.FFPP_ENABLED:
            return None
        if self._ffpp_model is not None:
            return self._ffpp_model, self._ffpp_processor

        configured_path = Path(settings.FFPP_MODEL_PATH)
        repo_root = Path(__file__).resolve().parent.parent.parent
        candidates = [configured_path] if configured_path.is_absolute() else [
            (repo_root / configured_path).resolve(),
            (Path.cwd() / configured_path).resolve(),
            (repo_root / "trained_models").resolve(),
        ]
        ckpt_path = next((p for p in candidates if (p / "config.json").exists()), candidates[0])

        if not (ckpt_path / "config.json").exists():
            tried = ", ".join(str(p) for p in candidates)
            logger.warning(f"FFPP ViT checkpoint not found. Tried: {tried} — skipping")
            return None

        try:
            from transformers import AutoImageProcessor, AutoModelForImageClassification

            logger.info(f"Loading FFPP ViT model from {ckpt_path}")
            processor = AutoImageProcessor.from_pretrained(settings.FFPP_BASE_PROCESSOR_ID)
            model = AutoModelForImageClassification.from_pretrained(str(ckpt_path))
            model.to(settings.DEVICE)
            model.eval()
            self._ffpp_model = model
            self._ffpp_processor = processor
            logger.info("FFPP ViT model loaded")
            return self._ffpp_model, self._ffpp_processor
        except Exception as e:
            logger.warning(f"FFPP ViT load failed (continuing without it): {e}")
            return None

    # ---------- Preload ----------
    def preload_phase1(self) -> None:
        """Preload only what Phase 1 needs (image model)."""
        self.load_image_model()

    def is_ready(self) -> bool:
        """Phase 19.5 — readiness signal for /health/ready.

        When PRELOAD_MODELS is enabled, readiness = image model loaded.
        Otherwise the loader constructs successfully → ready (lazy-load on demand).
        """
        if settings.PRELOAD_MODELS:
            return self._image_model is not None
        return True


def get_model_loader() -> ModelLoader:
    return ModelLoader.get_instance()

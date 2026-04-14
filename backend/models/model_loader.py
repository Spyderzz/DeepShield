from __future__ import annotations

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
                    cls._instance._text_pipeline = None
                    cls._instance._ocr_reader = None
                    cls._instance._face_detector = None
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

    # ---------- Text (BERT fake-news classifier) ----------
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

    # ---------- OCR (EasyOCR) ----------
    def load_ocr_engine(self):
        if self._ocr_reader is None:
            logger.info("Loading EasyOCR reader (en, hi)")
            import easyocr  # type: ignore

            self._ocr_reader = easyocr.Reader(["en", "hi"], gpu=(settings.DEVICE == "cuda"))
            logger.info("EasyOCR loaded")
        return self._ocr_reader

    # ---------- Face detector (MediaPipe) ----------
    def load_face_detector(self):
        if self._face_detector is None:
            logger.info("Loading MediaPipe FaceMesh")
            import mediapipe as mp  # type: ignore

            self._face_detector = mp.solutions.face_mesh.FaceMesh(
                static_image_mode=True,
                max_num_faces=5,
                min_detection_confidence=0.5,
            )
            logger.info("MediaPipe FaceMesh loaded")
        return self._face_detector

    # ---------- Preload ----------
    def preload_phase1(self) -> None:
        """Preload only what Phase 1 needs (image model)."""
        self.load_image_model()


def get_model_loader() -> ModelLoader:
    return ModelLoader.get_instance()

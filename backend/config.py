import json
from typing import Annotated, Any
from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    # Server
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    DEBUG: bool = False
    # NoDecode prevents pydantic-settings from forcing JSON parsing first.
    # This lets us accept JSON arrays, CSV strings, single origins, and empty values.
    CORS_ORIGINS: Annotated[list[str], NoDecode] = ["http://localhost:5173"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> list[str]:
        """Parse CORS_ORIGINS from string (JSON or comma-separated) into a list."""
        if v is None:
            return ["http://localhost:5173"]

        if isinstance(v, str):
            raw = v.strip()
            if not raw:
                return ["http://localhost:5173"]

            if raw.startswith("["):
                parsed = json.loads(raw)
                if isinstance(parsed, list):
                    return [str(i).strip() for i in parsed if str(i).strip()]

            # Supports single origin and comma-separated origins.
            return [i.strip() for i in raw.split(",") if i.strip()]

        if isinstance(v, list):
            return [str(i).strip() for i in v if str(i).strip()]

        return v

    # Database
    DATABASE_URL: str = "sqlite:///./deepshield.db"

    # File Upload
    MAX_UPLOAD_SIZE_MB: int = 100
    UPLOAD_DIR: str = "./temp_uploads"
    ALLOWED_IMAGE_TYPES: list[str] = ["image/jpeg", "image/png", "image/webp"]
    ALLOWED_VIDEO_TYPES: list[str] = ["video/mp4", "video/avi", "video/mov", "video/webm"]
    FILE_RETENTION_SECONDS: int = 300

    # AI Models
    IMAGE_MODEL_ID: str = "prithivMLmods/Deep-Fake-Detector-v2-Model"
    GENERAL_IMAGE_MODEL_ID: str = "umm-maybe/AI-image-detector"
    TEXT_MODEL_ID: str = "jy46604790/Fake-News-Bert-Detect"
    # Multilingual text model for non-English (Hindi etc.). Leave empty to fall back to TEXT_MODEL_ID.
    TEXT_MULTILANG_MODEL_ID: str = ""
    DEVICE: str = "cpu"
    PRELOAD_MODELS: bool = True  # preload models at startup

    # Phase 13: OCR language list (comma-separated ISO codes, e.g. "en,hi")
    OCR_LANGS: str = "en,hi"

    # News API
    NEWS_API_KEY: str = ""
    NEWS_API_BASE_URL: str = "https://newsdata.io/api/1/news"

    # Reports
    REPORT_DIR: str = "./temp_reports"
    REPORT_TTL_SECONDS: int = 3600  # 1h expiry

    # Phase 19 — dedup cache + object storage
    CACHE_TTL_DAYS: int = 30
    MEDIA_ROOT: str = "./media"

    # LLM Explainability (Phase 12)
    LLM_PROVIDER: str = "gemini"  # "gemini" | "openai"
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "gemini-2.5-flash"  # flash is ~12x cheaper + larger free-tier quota than pro. Use "gemini-2.5-pro" for harder reasoning.

    # LLM fallback — Groq (Llama 3.3 70B by default). Used automatically when the
    # primary provider returns 429/quota exceeded. Leave empty to disable fallback.
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    # EfficientNet (ICPR2020 / DeepShield1 merge)
    EFFICIENTNET_MODEL: str = "EfficientNetAutoAttB4"
    EFFICIENTNET_TRAIN_DB: str = "DFDC"
    ENSEMBLE_MODE: bool = True  # run both ViT + EfficientNet and average scores

    # Phase 11.3: FFPP-fine-tuned ViT. Path is resolved relative to the repo root.
    # The checkpoint lives at <repo_root>/trained_models/ (the `trained_models/` dir
    # at the project root, alongside `backend/` and `frontend/`).
    FFPP_MODEL_PATH: str = "trained_models"
    # Optional: pull FFPP checkpoint from Hugging Face Hub when local checkpoint
    # is missing (keeps large model files out of GitHub source repo).
    FFPP_MODEL_REPO_ID: str = ""
    FFPP_MODEL_REVISION: str = "main"
    FFPP_BASE_PROCESSOR_ID: str = "google/vit-base-patch16-224-in21k"
    FFPP_ENABLED: bool = True
    # Ensemble weights — FFPP is trained on a better (face-specific FFPP c40) dataset
    # and is weighted more heavily when a face is present. When no face is detected,
    # we still blend it but lean on the generic ViT since FFPP only saw face crops.
    FFPP_WEIGHT_FACE: float = 0.55       # face-present ensemble weight
    VIT_WEIGHT_FACE: float = 0.20
    EFFNET_WEIGHT_FACE: float = 0.25
    FFPP_WEIGHT_NOFACE: float = 0.35     # no-face ensemble weight
    VIT_WEIGHT_NOFACE: float = 0.65
    NOFACE_GENERAL_WEIGHT: float = 0.60
    NOFACE_FORENSICS_WEIGHT: float = 0.20
    NOFACE_EXIF_WEIGHT: float = 0.10
    NOFACE_VLM_WEIGHT: float = 0.10
    VIDEO_SAMPLE_FRAMES: int = 16  # frames to sample per video for inference
    EXIFTOOL_PATH: str = ""  # full path to ExifTool binary; empty = metadata write disabled

    # Auth
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 1440

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()

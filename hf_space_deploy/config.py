from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Server
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    DEBUG: bool = False
    CORS_ORIGINS: list[str] = ["http://localhost:5173"]

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

    # LLM Explainability (Phase 12)
    LLM_PROVIDER: str = "gemini"  # "gemini" | "openai"
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "gemini-2.5-pro"  # or "gpt-4o"

    # EfficientNet (ICPR2020 / DeepShield1 merge)
    EFFICIENTNET_MODEL: str = "EfficientNetAutoAttB4"
    EFFICIENTNET_TRAIN_DB: str = "DFDC"
    ENSEMBLE_MODE: bool = True  # run both ViT + EfficientNet and average scores
    VIDEO_SAMPLE_FRAMES: int = 16  # frames to sample per video for inference
    EXIFTOOL_PATH: str = ""  # full path to ExifTool binary; empty = metadata write disabled

    # Auth
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 1440

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()

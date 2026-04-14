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
    TEXT_MODEL_ID: str = "GonzaloA/fake-news-detection-small"
    DEVICE: str = "cpu"
    PRELOAD_MODELS: bool = True  # preload models at startup

    # News API
    NEWS_API_KEY: str = ""
    NEWS_API_BASE_URL: str = "https://newsdata.io/api/1/news"

    # Auth
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 1440

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()

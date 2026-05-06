from functools import lru_cache
from pathlib import Path

from pydantic import EmailStr, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    The defaults make local development easy. Production should override secrets,
    SMTP, Redis URLs, and disable CELERY_TASK_ALWAYS_EAGER.
    """

    PROJECT_NAME: str = "FastAPI Auth Blog"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_BASE_URL: str = "http://localhost:8000"

    DATABASE_URL: str = "sqlite+aiosqlite:///./app.db"
    DATABASE_ECHO: bool = False

    JWT_SECRET: str = Field(
        default="change-me-to-a-long-random-secret-at-least-32-characters",
        min_length=32,
    )
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS: int = 24
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 30

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_FAIL_OPEN: bool = True
    REDIS_BLACKLIST_URL: str | None = None
    REDIS_RATE_LIMIT_URL: str | None = None
    REDIS_CACHE_URL: str | None = None

    RATE_LIMIT_REQUESTS: int = 5
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    CELERY_BROKER_URL: str | None = None
    CELERY_RESULT_BACKEND: str | None = None
    CELERY_TASK_ALWAYS_EAGER: bool = True

    EMAILS_ENABLED: bool = False
    MAIL_USERNAME: str = ""
    MAIL_PASSWORD: str = ""
    MAIL_FROM: EmailStr | str = "noreply@example.com"
    MAIL_FROM_NAME: str = "FastAPI Auth Blog"
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_PORT: int = 587
    MAIL_STARTTLS: bool = True

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
    )

    @field_validator("JWT_ALGORITHM")
    @classmethod
    def validate_jwt_algorithm(cls, value: str) -> str:
        supported = {"HS256", "HS384", "HS512", "RS256", "RS384", "RS512"}
        if value not in supported:
            raise ValueError(f"JWT_ALGORITHM must be one of {supported}")
        return value

    @field_validator("REDIS_PORT", "MAIL_PORT")
    @classmethod
    def validate_port(cls, value: int) -> int:
        if not 1 <= value <= 65535:
            raise ValueError("Port must be between 1 and 65535")
        return value

    @property
    def redis_blacklist_url(self) -> str:
        return self.REDIS_BLACKLIST_URL or f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/3"

    @property
    def redis_rate_limit_url(self) -> str:
        return self.REDIS_RATE_LIMIT_URL or f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/5"

    @property
    def redis_cache_url(self) -> str:
        return self.REDIS_CACHE_URL or f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/5"

    @property
    def celery_broker_url(self) -> str:
        return self.CELERY_BROKER_URL or f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/4"

    @property
    def celery_result_backend(self) -> str:
        return self.CELERY_RESULT_BACKEND or f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/5"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

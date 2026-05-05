from typing import Optional
from pydantic import Field, field_validator, ConfigDict
from pydantic_settings import BaseSettings, SettingsConfigDict  # type: ignore

_base_config = SettingsConfigDict(
    env_file=".env",  # Correct parameter name for pydantic v2
    env_ignore_empty=True,
    extra="ignore"  # Ignore extra fields from .env
)


class DataBaseSettings(BaseSettings):
    """Database configuration settings."""
    
    DATABASE_URL: str = Field(..., description="PostgreSQL/MySQL connection URL")
    
    # Redis connection
    REDIS_HOST: str = Field(default="localhost", description="Redis host address")
    REDIS_PORT: int = Field(default=6379, description="Redis port number")

    model_config = _base_config
    
    @field_validator("REDIS_PORT")
    @classmethod
    def validate_redis_port(cls, v: int) -> int:
        """Validate Redis port is in valid range."""
        if not (1 <= v <= 65535):
            raise ValueError("Port must be between 1 and 65535")
        return v


class SecuritySettings(BaseSettings):
    """Security and authentication configuration settings."""
    
    JWT_SECRET: str = Field(..., min_length=32, description="JWT secret key (min 32 chars)")
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    JWT_EXPIRATION_HOURS: int = Field(default=24, description="JWT token expiration in hours")

    model_config = _base_config
    
    @field_validator("JWT_ALGORITHM")
    @classmethod
    def validate_jwt_algorithm(cls, v: str) -> str:
        """Validate JWT algorithm is supported."""
        supported_algorithms = {"HS256", "HS384", "HS512", "RS256", "RS384", "RS512"}
        if v not in supported_algorithms:
            raise ValueError(f"JWT_ALGORITHM must be one of {supported_algorithms}")
        return v


class MailSettings(BaseSettings):
    """Email/SMTP configuration settings."""
    
    MAIL_USERNAME: str = Field(..., description="SMTP username")
    MAIL_PASSWORD: str = Field(..., description="SMTP password")
    MAIL_FROM: str = Field(..., description="Sender email address")
    MAIL_FROM_NAME: str = Field(default="No Reply", description="Sender name")
    MAIL_SERVER: str = Field(default="smtp.gmail.com", description="SMTP server address")
    MAIL_PORT: int = Field(default=587, description="SMTP server port")

    model_config = _base_config
    
    @field_validator("MAIL_PORT")
    @classmethod
    def validate_mail_port(cls, v: int) -> int:
        """Validate mail port is in valid range."""
        if not (1 <= v <= 65535):
            raise ValueError("Port must be between 1 and 65535")
        return v


# Initialize settings - these will be loaded from .env file
db_settings = DataBaseSettings()
security_settings = SecuritySettings()
mail_settings = MailSettings()


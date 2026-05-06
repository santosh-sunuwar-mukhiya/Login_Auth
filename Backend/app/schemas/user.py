from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    username: str = Field(min_length=2, max_length=80)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    address: str | None = Field(default=None, max_length=255)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        has_letter = any(char.isalpha() for char in value)
        has_number = any(char.isdigit() for char in value)
        if not has_letter or not has_number:
            raise ValueError("Password must contain at least one letter and one number.")
        return value


class UserRead(BaseModel):
    id: UUID
    username: str
    email: EmailStr
    address: str | None
    is_email_verified: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

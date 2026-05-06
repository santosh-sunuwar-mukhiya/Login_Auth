from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import EmailStr
from sqlalchemy import Column, String, Text
from sqlmodel import Field, Relationship, SQLModel

from app.core.security import utc_now


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    username: str = Field(index=True, min_length=2, max_length=80)
    email: EmailStr = Field(
        sa_column=Column(String(320), unique=True, index=True, nullable=False)
    )
    address: str | None = Field(default=None, max_length=255)
    password_hash: str = Field(exclude=True, nullable=False)
    is_email_verified: bool = Field(default=False)
    is_active: bool = Field(default=True)
    token_version: int = Field(default=0)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    password_changed_at: datetime | None = None

    blogs: list["Blog"] = Relationship(back_populates="author")


class Blog(SQLModel, table=True):
    __tablename__ = "blogs"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    title: str = Field(index=True, min_length=1, max_length=160)
    content: str = Field(sa_column=Column(Text, nullable=False))
    author_id: UUID = Field(foreign_key="users.id", index=True)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    deleted_at: datetime | None = Field(default=None, index=True)

    author: User = Relationship(back_populates="blogs")

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

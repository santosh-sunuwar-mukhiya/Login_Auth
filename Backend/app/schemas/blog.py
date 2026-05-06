from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class BlogCreate(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    content: str = Field(min_length=1)


class BlogUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=160)
    content: str | None = Field(default=None, min_length=1)


class BlogRead(BaseModel):
    id: UUID
    title: str
    content: str
    author_id: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class BlogList(BaseModel):
    items: list[BlogRead]
    total: int
    limit: int
    offset: int

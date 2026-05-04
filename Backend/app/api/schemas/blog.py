from uuid import UUID

from pydantic import BaseModel # type: ignore

class BlogBase(BaseModel):
    content: str

class BlogCreate(BlogBase):
    pass

class BlogRead(BlogBase):
    id:UUID
    user_id: UUID
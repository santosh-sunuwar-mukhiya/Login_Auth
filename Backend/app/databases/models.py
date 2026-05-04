from datetime import datetime
from uuid import UUID, uuid4
from pydantic import EmailStr # type: ignore
from sqlmodel import SQLModel, Field, Column, Relationship # type: ignore

class User(SQLModel, table=True): # type: ignore

    __tablename__ = "user"

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
    )

    username: str 
    email: EmailStr = Field(unique=True)
    address: str
    verified_email: bool = Field(default=False)
    password_hash: str = Field(exclude=True)

    blogs: list["Blog"] = Relationship(back_populates="user", sa_relationship_kwargs={"lazy":"selectin"},) # type: ignore


class Blog(SQLModel, table=True): # type: ignore

    __tablename__ = "blog"

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
    )

    content: str 
    created_at: datetime = Field(default_factory=datetime.now)

    user_id: UUID = Field(foreign_key="user.id")

    user: "User" = Relationship(back_populates="blogs", sa_relationship_kwargs={"lazy":"selectin"},)



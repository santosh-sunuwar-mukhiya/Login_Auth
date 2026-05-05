from uuid import UUID

from pydantic import BaseModel, EmailStr # type: ignore

class UserBase(BaseModel): # type: ignore
    email: EmailStr # type: ignore
    username: str
    

class UserCreate(UserBase):
    password: str
    address: str
    username: str

class UserRead(UserBase):
    id: UUID
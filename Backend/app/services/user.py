from datetime import datetime, timedelta, timezone

from ..api.schemas.user import UserCreate
from ..databases.models import User
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore
from pwdlib import PasswordHash # type: ignore
from sqlalchemy import select # type: ignore
from fastapi import HTTPException, status # type: ignore
import jwt # type: ignore
from pydantic import EmailStr # type: ignore
from ..config import SecuritySettings


pwd_hasher = PasswordHash.recommended()
security_settings = SecuritySettings()  # type: ignore

class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, create_user: UserCreate) -> User: # type: ignore
        user = User(
            **create_user.model_dump(exclude=["password"]),
            password_hash = pwd_hasher.hash(create_user.password)
        )

        self.session.add(user) # type: ignore
        await self.session.commit()
        await self.session.refresh(user)

        return user
    
    async def token(self, email: EmailStr, password: str) -> str: # type: ignore
        result = await self.session.execute(select(User).where(User.email == email))
        user = result.scalar()

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email or Password is wrong."
            )
        
        try:
            password_check = pwd_hasher.verify(password, user.password_hash)

        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email or Password is wrong."
            )
        
        if not password_check:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email or Password is wrong."
            )
        

        token = jwt.encode( # type: ignore
            payload={
                "user":{
                    "name": user.username,
                    "email": user.email,
                },
                "exp": datetime.now(timezone.utc) + timedelta(minutes=15)
            },
            algorithm=security_settings.JWT_ALGORITHM,
            key=security_settings.JWT_SECRET,
        )

        return token
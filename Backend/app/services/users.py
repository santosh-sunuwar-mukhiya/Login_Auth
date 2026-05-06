from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, utc_now
from app.db.models import User
from app.schemas.user import UserCreate


class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: UUID) -> User | None:
        return await self.session.get(User, user_id)

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(
            select(User).where(User.email == email.lower())
        )
        return result.scalar_one_or_none()

    async def create(self, payload: UserCreate) -> User:
        if await self.get_by_email(str(payload.email)):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this email already exists.",
            )

        user = User(
            username=payload.username,
            email=str(payload.email).lower(),
            address=payload.address,
            password_hash=hash_password(payload.password),
        )
        self.session.add(user)
        try:
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this email already exists.",
            ) from exc

        await self.session.refresh(user)
        return user

    async def mark_email_verified(self, user: User) -> User:
        if not user.is_email_verified:
            user.is_email_verified = True
            user.updated_at = utc_now()
            self.session.add(user)
            await self.session.commit()
            await self.session.refresh(user)
        return user

    async def update_password(self, user: User, new_password: str) -> User:
        user.password_hash = hash_password(new_password)
        user.token_version += 1
        user.password_changed_at = utc_now()
        user.updated_at = utc_now()
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

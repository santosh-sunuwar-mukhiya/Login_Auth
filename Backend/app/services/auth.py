from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_email_verification_token,
    create_password_reset_token,
    create_refresh_token,
    decode_jwt_token,
    require_token_type,
    verify_password,
)
from app.db.models import User
from app.schemas.auth import TokenPair
from app.schemas.user import UserCreate
from app.services.email import queue_password_reset_email, queue_verification_email
from app.services.token_blacklist import blacklist_token, is_token_blacklisted
from app.services.users import UserService


class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.users = UserService(session)

    async def register(self, payload: UserCreate) -> User:
        user = await self.users.create(payload)
        token = create_email_verification_token(user.id, user.token_version)
        verification_link = f"{settings.API_BASE_URL}/auth/verify-email?token={token}"
        queue_verification_email(str(user.email), verification_link)
        return user

    async def login(self, email: str, password: str) -> TokenPair:
        user = await self.users.get_by_email(email)
        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email or password is incorrect.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_email_verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Please verify your email before logging in.",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This account is inactive.",
            )

        return self._build_token_pair(user)

    async def verify_email(self, token: str) -> str:
        payload = decode_jwt_token(token)
        require_token_type(payload, "email_verification")
        user = await self._get_user_from_payload(payload)
        await self.users.mark_email_verified(user)
        return "Email verified successfully. You can now log in."

    async def refresh(self, refresh_token: str) -> TokenPair:
        payload = decode_jwt_token(refresh_token)
        require_token_type(payload, "refresh")
        if await is_token_blacklisted(payload["jti"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has been revoked.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user = await self._get_user_from_payload(payload)
        await blacklist_token(payload["jti"], payload["exp"])
        return self._build_token_pair(user)

    async def logout(self, access_token: str, refresh_token: str | None = None) -> str:
        access_payload = decode_jwt_token(access_token)
        require_token_type(access_payload, "access")
        await blacklist_token(access_payload["jti"], access_payload["exp"])

        if refresh_token:
            refresh_payload = decode_jwt_token(refresh_token)
            require_token_type(refresh_payload, "refresh")
            await blacklist_token(refresh_payload["jti"], refresh_payload["exp"])

        return "Logged out successfully."

    async def request_password_reset(self, email: str) -> str:
        user = await self.users.get_by_email(email)
        if user and user.is_active:
            token = create_password_reset_token(user.id, user.token_version)
            reset_link = f"{settings.API_BASE_URL}/auth/reset-password?token={token}"
            queue_password_reset_email(str(user.email), reset_link)

        # Generic response prevents attackers from discovering registered emails.
        return "If that email is registered, a password reset link has been sent."

    async def reset_password(self, token: str, new_password: str) -> str:
        payload = decode_jwt_token(token)
        require_token_type(payload, "password_reset")
        user = await self._get_user_from_payload(payload)
        await self.users.update_password(user, new_password)
        await blacklist_token(payload["jti"], payload["exp"])
        return "Password reset successfully. Please log in again."

    def _build_token_pair(self, user: User) -> TokenPair:
        return TokenPair(
            access_token=create_access_token(user.id, user.token_version),
            refresh_token=create_refresh_token(user.id, user.token_version),
        )

    async def _get_user_from_payload(self, payload: dict) -> User:
        user = await self.users.get_by_id(payload["sub"])
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User no longer exists.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if payload.get("ver") != user.token_version:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token is no longer valid.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This account is inactive.",
            )

        return user

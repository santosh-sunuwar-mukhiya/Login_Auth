from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_jwt_token, oauth2_scheme, require_token_type
from app.db.models import User
from app.db.session import get_session
from app.services.auth import AuthService
from app.services.blogs import BlogService
from app.services.token_blacklist import is_token_blacklisted
from app.services.users import UserService

SessionDep = Annotated[AsyncSession, Depends(get_session)]

AccessTokenDep = Annotated[str, Depends(oauth2_scheme)]


def get_user_service(session: SessionDep) -> UserService:
    return UserService(session)


def get_auth_service(session: SessionDep) -> AuthService:
    return AuthService(session)


def get_blog_service(session: SessionDep) -> BlogService:
    return BlogService(session)


async def get_current_user(token: AccessTokenDep, session: SessionDep) -> User:
    payload = decode_jwt_token(token)
    require_token_type(payload, "access")

    if await is_token_blacklisted(payload["jti"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = UUID(payload["sub"])
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token subject.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    user = await UserService(session).get_by_id(user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if payload.get("ver") != user.token_version:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is no longer valid.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


UserServiceDep = Annotated[UserService, Depends(get_user_service)]
AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
BlogServiceDep = Annotated[BlogService, Depends(get_blog_service)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]

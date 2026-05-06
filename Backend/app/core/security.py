from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID, uuid4

import jwt
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt import ExpiredSignatureError, InvalidTokenError
from pwdlib import PasswordHash

from .config import settings


pwd_hasher = PasswordHash.recommended()

# Swagger/OpenAPI uses tokenUrl to know where users exchange email+password
# for a Bearer token. Endpoints read the actual token from Authorization.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def hash_password(password: str) -> str:
    return pwd_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return pwd_hasher.verify(password, password_hash)
    except Exception:
        return False


def create_jwt_token(
    *,
    subject: UUID | str,
    token_type: str,
    expires_delta: timedelta,
    token_version: int,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    now = utc_now()
    payload: dict[str, Any] = {
        "sub": str(subject),
        "type": token_type,
        "ver": token_version,
        "jti": str(uuid4()),
        "iat": now,
        "exp": now + expires_delta,
    }
    if extra_claims:
        payload.update(extra_claims)

    return jwt.encode(
        payload,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_jwt_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    required_claims = {"sub", "type", "ver", "jti", "exp"}
    if not required_claims.issubset(payload):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is missing required claims.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload


def create_access_token(user_id: UUID, token_version: int) -> str:
    return create_jwt_token(
        subject=user_id,
        token_type="access",
        token_version=token_version,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )


def create_refresh_token(user_id: UUID, token_version: int) -> str:
    return create_jwt_token(
        subject=user_id,
        token_type="refresh",
        token_version=token_version,
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )


def create_email_verification_token(user_id: UUID, token_version: int) -> str:
    return create_jwt_token(
        subject=user_id,
        token_type="email_verification",
        token_version=token_version,
        expires_delta=timedelta(hours=settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS),
    )


def create_password_reset_token(user_id: UUID, token_version: int) -> str:
    return create_jwt_token(
        subject=user_id,
        token_type="password_reset",
        token_version=token_version,
        expires_delta=timedelta(minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES),
    )


def require_token_type(payload: dict[str, Any], expected_type: str) -> None:
    if payload.get("type") != expected_type:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Expected a {expected_type} token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

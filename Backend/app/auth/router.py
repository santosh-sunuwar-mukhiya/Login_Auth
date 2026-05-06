from typing import Annotated

from fastapi import APIRouter, Body, Depends, Query, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.dependencies import AccessTokenDep, AuthServiceDep, CurrentUserDep
from app.core.rate_limit import rate_limit
from app.schemas.auth import (
    ForgotPasswordRequest,
    LogoutRequest,
    RefreshTokenRequest,
    ResetPasswordRequest,
    TokenPair,
)
from app.schemas.common import MessageResponse
from app.schemas.user import UserCreate, UserRead

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit("register"))],
)
async def register_user(payload: UserCreate, service: AuthServiceDep):
    return await service.register(payload)


@router.post(
    "/login",
    response_model=TokenPair,
    dependencies=[Depends(rate_limit("login"))],
)
async def login_user(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    service: AuthServiceDep,
):
    # OAuth2PasswordRequestForm names the login field "username".
    # In this app, users enter their email address there.
    return await service.login(form.username, form.password)


@router.get("/verify-email", response_model=MessageResponse)
async def verify_email(
    service: AuthServiceDep,
    token: str = Query(..., min_length=20),
):
    message = await service.verify_email(token)
    return MessageResponse(message=message)


@router.post("/refresh", response_model=TokenPair)
async def refresh_token(payload: RefreshTokenRequest, service: AuthServiceDep):
    return await service.refresh(payload.refresh_token)


@router.post("/logout", response_model=MessageResponse)
async def logout_user(
    service: AuthServiceDep,
    access_token: AccessTokenDep,
    _: CurrentUserDep,
    payload: LogoutRequest | None = Body(default=None),
):
    refresh_token = payload.refresh_token if payload else None
    message = await service.logout(access_token, refresh_token)
    return MessageResponse(message=message)


@router.post(
    "/forgot-password",
    response_model=MessageResponse,
    dependencies=[Depends(rate_limit("forgot-password"))],
)
async def forgot_password(payload: ForgotPasswordRequest, service: AuthServiceDep):
    message = await service.request_password_reset(str(payload.email))
    return MessageResponse(message=message)


@router.post(
    "/reset-password",
    response_model=MessageResponse,
    dependencies=[Depends(rate_limit("reset-password"))],
)
async def reset_password(payload: ResetPasswordRequest, service: AuthServiceDep):
    message = await service.reset_password(payload.token, payload.new_password)
    return MessageResponse(message=message)

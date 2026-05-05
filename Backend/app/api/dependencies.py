from typing import Annotated
from fastapi import Depends # type: ignore
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore
from ..databases.session import get_session
from ..services.user import UserService

SessionDep = Annotated[AsyncSession, Depends(get_session)]

def get_user_service(session: SessionDep): # type: ignore
    return UserService(session) # type: ignore


UserServiceDep = Annotated[UserService, Depends(get_user_service)]
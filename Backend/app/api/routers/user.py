from typing import Annotated
from ..schemas.user import UserRead, UserCreate # type: ignore
from ..dependencies import UserServiceDep # type: ignore
from fastapi import APIRouter, status, Depends # type: ignore
from fastapi.security import OAuth2PasswordRequestForm # type: ignore

router = APIRouter(prefix="/users", tags=["users"])



@router.post("/SignUp", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register_user(service: UserServiceDep, create_user: UserCreate):
   return await service.add(create_user)


@router.post("/Login")
async def login_user(request_form: Annotated[OAuth2PasswordRequestForm, Depends()], service: UserServiceDep):
   token = await service.token(
      request_form.username, 
      request_form.password
   )

   return {
      "token": token,
      "type": "jwt"
   }




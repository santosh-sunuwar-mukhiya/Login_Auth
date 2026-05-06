from fastapi import APIRouter # type: ignore

from app.auth.router import router as auth_router
from app.blogs.router import router as blog_router
from app.users.router import router as user_router

master_router = APIRouter()
master_router.include_router(auth_router)
master_router.include_router(user_router)
master_router.include_router(blog_router)

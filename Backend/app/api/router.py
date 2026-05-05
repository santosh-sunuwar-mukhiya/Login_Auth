from fastapi import APIRouter # type: ignore
from .routers.user import router as user_router
from .routers.blog import router as blog_router

master_router = APIRouter()
master_router.include_router(user_router)
master_router.include_router(blog_router)
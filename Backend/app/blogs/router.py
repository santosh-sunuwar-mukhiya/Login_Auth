from uuid import UUID

from fastapi import APIRouter, Query, Response, status

from app.api.dependencies import BlogServiceDep, CurrentUserDep
from app.core.redis import cache_get_json, cache_set_json
from app.schemas.blog import BlogCreate, BlogList, BlogRead, BlogUpdate

router = APIRouter(prefix="/blogs", tags=["blogs"])


@router.get("/", response_model=BlogList)
async def list_blogs(
    service: BlogServiceDep,
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    cache_key = f"blogs:list:{limit}:{offset}"
    cached = await cache_get_json(cache_key)
    if cached:
        return cached

    blogs = await service.list_public(limit=limit, offset=offset)
    await cache_set_json(cache_key, blogs.model_dump(mode="json"), ttl_seconds=30)
    return blogs


@router.get("/{blog_id}", response_model=BlogRead)
async def get_blog(blog_id: UUID, service: BlogServiceDep):
    return await service.get_public(blog_id)


@router.post("/", response_model=BlogRead, status_code=status.HTTP_201_CREATED)
async def create_blog(
    payload: BlogCreate,
    service: BlogServiceDep,
    current_user: CurrentUserDep,
):
    return await service.create(payload, current_user)


@router.patch("/{blog_id}", response_model=BlogRead)
async def update_blog(
    blog_id: UUID,
    payload: BlogUpdate,
    service: BlogServiceDep,
    current_user: CurrentUserDep,
):
    return await service.update(blog_id, payload, current_user)


@router.delete("/{blog_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_blog(
    blog_id: UUID,
    service: BlogServiceDep,
    current_user: CurrentUserDep,
):
    await service.soft_delete(blog_id, current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

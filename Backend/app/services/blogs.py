from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import cache_delete_pattern
from app.core.security import utc_now
from app.db.models import Blog, User
from app.schemas.blog import BlogCreate, BlogList, BlogUpdate


class BlogService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_public(self, *, limit: int, offset: int) -> BlogList:
        filters = Blog.deleted_at.is_(None)

        total_result = await self.session.execute(
            select(func.count()).select_from(Blog).where(filters)
        )
        total = total_result.scalar_one()

        result = await self.session.execute(
            select(Blog)
            .where(filters)
            .order_by(Blog.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        blogs = list(result.scalars().all())
        return BlogList(items=blogs, total=total, limit=limit, offset=offset)

    async def get_public(self, blog_id: UUID) -> Blog:
        blog = await self.session.get(Blog, blog_id)
        if not blog or blog.deleted_at is not None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Blog not found.",
            )
        return blog

    async def create(self, payload: BlogCreate, author: User) -> Blog:
        blog = Blog(
            title=payload.title,
            content=payload.content,
            author_id=author.id,
        )
        self.session.add(blog)
        await self.session.commit()
        await self.session.refresh(blog)
        await self._invalidate_cache()
        return blog

    async def update(self, blog_id: UUID, payload: BlogUpdate, author: User) -> Blog:
        blog = await self._get_owned_blog(blog_id, author)
        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(blog, field, value)
        blog.updated_at = utc_now()
        self.session.add(blog)
        await self.session.commit()
        await self.session.refresh(blog)
        await self._invalidate_cache()
        return blog

    async def soft_delete(self, blog_id: UUID, author: User) -> None:
        blog = await self._get_owned_blog(blog_id, author)
        blog.deleted_at = utc_now()
        blog.updated_at = utc_now()
        self.session.add(blog)
        await self.session.commit()
        await self._invalidate_cache()

    async def _get_owned_blog(self, blog_id: UUID, author: User) -> Blog:
        blog = await self.session.get(Blog, blog_id)
        if not blog or blog.deleted_at is not None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Blog not found.",
            )

        if blog.author_id != author.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the blog owner can modify this blog.",
            )

        return blog

    async def _invalidate_cache(self) -> None:
        await cache_delete_pattern("blogs:list:*")

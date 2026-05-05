from fastapi import APIRouter # type: ignore


router = APIRouter(prefix="/blog", tags=["blog"])


@router.get("/")
async def get_blog_router() -> dict[str, str]:
	return {"message": "blog router ready"}

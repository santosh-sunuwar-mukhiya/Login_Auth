from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from scalar_fastapi import get_scalar_api_reference

from app.api.router import master_router
from app.core.config import settings
from app.core.logging import configure_logging
from app.db.session import create_db_tables

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    logger.info("Starting %s", settings.PROJECT_NAME)
    await create_db_tables()
    yield
    logger.info("Stopping %s", settings.PROJECT_NAME)


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(master_router)

@app.get("/")
async def root():
    return {"message": "FastAPI authentication and blog API is running."}


@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok"}

@app.get("/scalar", include_in_schema=False)
async def scalar_docs() -> HTMLResponse:
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        title=app.title,
    )

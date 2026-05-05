from .databases.session import create_db_tables # type: ignore
from fastapi import FastAPI # type: ignore
from fastapi.responses import HTMLResponse # type: ignore
from scalar_fastapi import get_scalar_api_reference # type: ignore
from contextlib import asynccontextmanager
from .api.router import master_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Server Started...")
    await create_db_tables()
    yield
    print("Server Stopped...")


app = FastAPI(lifespan=lifespan)

app.include_router(master_router)

# Sample route
@app.get("/")
async def root():
    return {"message": "Hello World"}

# Scalar Docs Endpoint
@app.get("/scalar", include_in_schema=False)
async def scalar_docs() -> HTMLResponse:
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        title=app.title,
    )
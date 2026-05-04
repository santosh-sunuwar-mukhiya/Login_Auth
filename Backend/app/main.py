from fastapi import FastAPI # type: ignore
from fastapi.responses import HTMLResponse # type: ignore
from scalar_fastapi import get_scalar_api_reference # type: ignore

app = FastAPI(
    title="My FastAPI App",
    version="1.0.0",
    docs_url=None,        # disable default Swagger UI
    redoc_url=None        # disable ReDoc
)

# Sample route
@app.get("/")
async def root():
    return {"message": "Hello World"}

# Scalar Docs Endpoint
@app.get("/docs", include_in_schema=False)
async def scalar_docs() -> HTMLResponse:
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        title=app.title,
    )
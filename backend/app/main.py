
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from .api.v1.sandboxes import router as sandboxes_router
from .api.v1.auth import router as auth_router
from .api.v1.projects import router as projects_router

app = FastAPI(title="USaD API", version="0.1.0")

app.include_router(sandboxes_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(projects_router, prefix="/api/v1")


@app.get("/api/v1/health")
def health() -> JSONResponse:
    return JSONResponse({"status": "ok", "service": "usad-api"})

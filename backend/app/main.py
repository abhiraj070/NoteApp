import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from . import schema  # Register the ORM models with the shared database metadata.
from .api import router


app = FastAPI(title="NotesAPP")
allowed_origins = [origin.strip().rstrip("/") for origin in os.getenv("ALLOWED_ORIGINS", "").split(",") if origin.strip()]
if allowed_origins:
    app.add_middleware(CORSMiddleware, allow_origins=allowed_origins, allow_credentials=True,
                       allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE"], allow_headers=["Content-Type"])


@app.middleware("http")
async def protect_cookie_requests(request: Request, call_next):
    if request.method not in ("GET", "HEAD", "OPTIONS"):
        origin = request.headers.get("origin")
        trusted = allowed_origins + [str(request.base_url).rstrip("/")]
        if (origin and origin.rstrip("/") not in trusted) or (not origin and request.headers.get("sec-fetch-site") == "cross-site"):
            return JSONResponse(status_code=403, content={"detail": "Untrusted request origin"})
    response = await call_next(request)
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    return response


app.include_router(router)


@app.get("/health")
def health():
    return {"status": "ok"}

import logging
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import app.scraping.sites  # noqa: F401  (import side-effect: register site adapters)
from app.api.routes import admin, auth, billing, images, listings, meta, parking
from app.core import ratelimit
from app.core.config import settings
from app.db.base import init_db

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="RentScalper API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def global_rate_limit(request: Request, call_next):
    """Coarse per-IP flood protection across the whole API. Endpoint-specific
    limits (auth, billing, images) sit on top of this one."""
    limit = settings.global_rate_limit_per_min
    if limit > 0 and request.url.path.startswith("/api"):
        ip = request.client.host if request.client else "?"
        if ip in ("127.0.0.1", "::1"):
            # behind the reverse proxy (Caddy/Cloudflare) the peer is localhost;
            # the proxy is trusted to set the real client in X-Forwarded-For
            fwd = request.headers.get("x-forwarded-for", "")
            if fwd:
                ip = fwd.split(",")[0].strip()
        if not ratelimit.allow(f"global:{ip}", limit):
            return JSONResponse(
                status_code=429,
                content={"detail": "Prea multe cereri. Reîncearcă în scurt timp."},
            )
    return await call_next(request)

api = APIRouter(prefix="/api")
for r in (
    listings.router,
    parking.router,
    meta.router,
    images.router,
    admin.router,
    auth.router,
    billing.router,
):
    api.include_router(r)


@api.get("/health")
def health():
    from sqlalchemy import text

    from app.db.base import SessionLocal

    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
        return {"status": "ok", "db": True}
    except Exception:
        return {"status": "degraded", "db": False}


app.include_router(api)

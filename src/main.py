"""
main.py
=======
Customer Health Forensics System — Phase 6
FastAPI application entry point.

Startup:
  uvicorn main:app --host 0.0.0.0 --port 3000 --reload
"""

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from core.config   import get_settings
from core.database import init_db
from utils.logger  import log

from api.routes import (
    health, predict, explain, upload,
    segments, drift, insights, models,
    customers, reports, pipeline, admin,
)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    log.info(f"[Startup] {settings.APP_NAME} v{settings.APP_VERSION}")
    log.info(f"[Startup] Database: {settings.DATABASE_URL[:40]}...")
    await init_db()
    log.info("[Startup] Database tables ready.")
    yield
    log.info("[Shutdown] API shutting down.")


app = FastAPI(
    title       = settings.APP_NAME,
    version     = settings.APP_VERSION,
    description = (
        "End-to-end Customer Health Forensics REST API. "
        "Prediction → XAI → Segmentation → Drift → Insights → Reports."
    ),
    docs_url    = "/docs",
    redoc_url   = "/redoc",
    lifespan    = lifespan,
)

# ── CORS ──────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins     = ["*"],   # restrict in production
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)


# ── Request logging middleware ────────────────────────────────
@app.middleware("http")
async def log_requests(request: Request, call_next):
    t0       = time.time()
    response = await call_next(request)
    elapsed  = round((time.time() - t0) * 1000, 1)
    log.info(
        f"{request.method} {request.url.path} → "
        f"{response.status_code} ({elapsed}ms)"
    )
    return response


# ── Global error handler ──────────────────────────────────────
@app.exception_handler(Exception)
async def global_error_handler(request: Request, exc: Exception):
    log.error(f"Unhandled error on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
        content     = {"error": "Internal server error", "detail": str(exc), "code": 500},
    )


# ── Route registration ────────────────────────────────────────
# System
app.include_router(health.router)
app.include_router(admin.router)

# Core pipeline
app.include_router(upload.router)
app.include_router(pipeline.router)
app.include_router(predict.router)
app.include_router(explain.router)

# Analysis
app.include_router(segments.router)
app.include_router(drift.router)
app.include_router(insights.router)

# Customer intelligence
app.include_router(customers.router)

# Models + Reports
app.include_router(models.router)
app.include_router(reports.router)


# ── Root ──────────────────────────────────────────────────────
@app.get("/", tags=["System"])
async def root():
    return {
        "service":  settings.APP_NAME,
        "version":  settings.APP_VERSION,
        "docs":     "/docs",
        "health":   "/health",
        "workflow": "Upload → /upload | Predict → /predict | "
                    "Explain → /explain | Segments → /segments | "
                    "Drift → /drift | Insights → /insights",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host    = settings.HOST,
        port    = settings.PORT,
        reload  = settings.DEBUG,
        workers = 1,
    )

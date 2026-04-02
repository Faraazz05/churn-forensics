# ══════════════════════════════════════════════════════════════
# Customer Health Forensics — Backend Dockerfile
# Phase 8: Production deployment
#
# Build:  docker build -f backend/Dockerfile -t churn-api .
# Run:    docker run -p 3000:3000 --env-file .env churn-api
# ══════════════════════════════════════════════════════════════

FROM python:3.11-slim AS base

# Build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc g++ libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ── Dependency layer (cached separately) ──────────────────────
FROM base AS dependencies
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ── Final image ────────────────────────────────────────────────
FROM base AS production

# Copy installed packages from dependency layer
COPY --from=dependencies /usr/local/lib/python3.11/site-packages \
                         /usr/local/lib/python3.11/site-packages
COPY --from=dependencies /usr/local/bin /usr/local/bin

# Copy application source
COPY src/ ./src/
COPY backend/src/ ./src/

# Create runtime directories
RUN mkdir -p /app/models /app/data /app/outputs/xai \
             /app/outputs/segmentation /app/outputs/drift \
             /app/outputs/insights /app/outputs/reports \
             /app/uploads /app/logs

# Environment
ENV PYTHONPATH=/app/src \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOST=0.0.0.0 \
    PORT=3000 \
    LOG_LEVEL=INFO \
    LLM_MODE=rules \
    DATABASE_URL=sqlite:////app/customer_health.db

# Non-root user for security
RUN useradd -m -u 1000 appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:3000/health || exit 1

# Run with 2 workers (increase for production based on CPU cores)
CMD ["uvicorn", "main:app", \
     "--host", "0.0.0.0", \
     "--port", "3000", \
     "--workers", "2", \
     "--log-level", "info", \
     "--app-dir", "/app/src", \
     "--access-log"]

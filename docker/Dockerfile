FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc g++ libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy backend source files into /app/src
COPY src/ ./src/

# Copy phase runner scripts (used by background pipeline tasks)
COPY insight_runner.py ./insight_runner.py
COPY run_full_pipeline.py ./run_full_pipeline.py

# Create all runtime directories with correct permissions
RUN mkdir -p /app/models /app/data /app/outputs/xai \
             /app/outputs/segmentation /app/outputs/drift \
             /app/outputs/insights /app/outputs/reports \
             /app/uploads /app/logs

# Set environment
ENV PYTHONPATH=/app/src \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOST=0.0.0.0 \
    PORT=3000 \
    LOG_LEVEL=INFO \
    LLM_MODE=rules \
    DATABASE_URL=sqlite:////app/customer_health.db

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:3000/health || exit 1

# Run as root (volumes mounted from Windows need root inside container)
CMD ["uvicorn", "main:app", \
     "--host", "0.0.0.0", \
     "--port", "3000", \
     "--workers", "2", \
     "--log-level", "info", \
     "--app-dir", "/app/src"]
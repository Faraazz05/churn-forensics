"""
core/config.py
==============
Centralised configuration — all settings from environment variables.
"""

from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # ── App ──────────────────────────────────────────────────────
    APP_NAME:    str = "Customer Health Forensics API"
    APP_VERSION: str = "1.0.0"
    DEBUG:       bool = False
    HOST:        str = "0.0.0.0"
    PORT:        int = 3000

    # ── Database ─────────────────────────────────────────────────
    DATABASE_URL: str = "sqlite:///./customer_health.db"
    # For PostgreSQL: postgresql+asyncpg://user:pass@host:5432/dbname

    # ── Auth ─────────────────────────────────────────────────────
    API_KEY_ADMIN:     str = "admin-secret-key-change-in-production"
    API_KEY_READONLY:  str = "readonly-key-change-in-production"
    API_KEY_HEADER:    str = "X-API-Key"

    # ── Phase artifact paths ──────────────────────────────────────
    # These point to where each phase stores its outputs.
    BASE_DIR:         Path = Path(__file__).resolve().parent.parent.parent.parent
    MODELS_DIR:       Path = BASE_DIR / "models"
    DATA_DIR:         Path = BASE_DIR / "data"
    OUTPUTS_DIR:      Path = BASE_DIR / "outputs"
    UPLOAD_DIR:       Path = BASE_DIR / "uploads"
    REPORTS_DIR:      Path = BASE_DIR / "outputs" / "reports"

    # ── Phase source directories ──────────────────────────────────
    PHASE1_SRC:  Path = BASE_DIR / "src"
    PHASE2_SRC:  Path = BASE_DIR / "src"
    PHASE3_SRC:  Path = BASE_DIR / "src"
    PHASE4_SRC:  Path = BASE_DIR / "src"
    PHASE5_SRC:  Path = BASE_DIR / "src"

    # ── Pipeline ─────────────────────────────────────────────────
    MAX_UPLOAD_SIZE_MB: int  = 500
    PIPELINE_TIMEOUT_S: int  = 1800   # 30 min

    # ── LLM ──────────────────────────────────────────────────────
    LLM_MODE:    str = "rules"    # rules / api / local
    LLM_MODEL_ID: str = "mistralai/Mistral-7B-Instruct-v0.2"
    HUGGINGFACEHUB_API_TOKEN: str = ""

    # ── Logging ──────────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"
    LOG_FILE:  Path = BASE_DIR / "logs" / "api.log"

    # ── Watchlist ─────────────────────────────────────────────────
    WATCHLIST_THRESHOLD: float = 0.70

    def ensure_dirs(self):
        for d in [self.UPLOAD_DIR, self.REPORTS_DIR, self.OUTPUTS_DIR,
                  self.LOG_FILE.parent]:
            d.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    s.ensure_dirs()
    return s

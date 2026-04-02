"""
services/upload_service.py
===========================
Handles file ingestion — reads, validates, and stores uploaded data.
"""
import shutil
from pathlib import Path
import pandas as pd

from core.config import get_settings
from utils.logger import log

settings = get_settings()

REQUIRED_COLS = {"customer_id", "churned"}


def ingest_dataframe(df: pd.DataFrame, upload_id: str) -> dict:
    """
    Validate and store uploaded DataFrame to data directory.
    Returns ingestion summary.
    """
    missing = REQUIRED_COLS - set(df.columns)
    if missing:
        log.warning(f"[UploadService] Missing columns: {missing} — proceeding anyway")

    # Save to data dir for pipeline consumption
    dest = settings.DATA_DIR / "customers.csv"
    settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(dest, index=False)

    churn_rate = float(df["churned"].mean()) if "churned" in df.columns else None
    log.info(f"[UploadService] {len(df):,} rows saved to {dest}")

    return {
        "rows_ingested": len(df),
        "churn_rate":    round(churn_rate, 4) if churn_rate else None,
        "columns":       list(df.columns),
    }

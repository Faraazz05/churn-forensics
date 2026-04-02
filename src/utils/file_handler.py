"""
utils/file_handler.py
=====================
Upload validation, storage, and parsing for CSV / Excel files.
"""

import hashlib
import shutil
from pathlib import Path
from typing import Optional

import pandas as pd
from fastapi import HTTPException, UploadFile, status

from core.config import get_settings
from utils.logger import log

settings = get_settings()

ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls"}
MAX_BYTES = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024


async def validate_and_save(file: UploadFile) -> tuple[Path, str]:
    """
    Validate file type + size and persist to uploads dir.

    Returns:
        (saved_path, original_filename)
    """
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type '{suffix}'. "
                   f"Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # Stream to temp path while checking size
    content = await file.read()
    if len(content) > MAX_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds {settings.MAX_UPLOAD_SIZE_MB} MB limit.",
        )

    # Unique filename via content hash
    digest   = hashlib.md5(content).hexdigest()[:8]
    filename = f"{digest}{suffix}"
    dest     = settings.UPLOAD_DIR / filename
    dest.write_bytes(content)

    log.info(f"[FileHandler] Saved upload: {filename} ({len(content)/1e6:.1f} MB)")
    return dest, file.filename or filename


def read_dataframe(path: Path) -> pd.DataFrame:
    """Read CSV or Excel into a DataFrame with basic validation."""
    suffix = path.suffix.lower()
    try:
        if suffix == ".csv":
            df = pd.read_csv(path)
        elif suffix in (".xlsx", ".xls"):
            df = pd.read_excel(path)
        else:
            raise ValueError(f"Unsupported: {suffix}")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Could not parse file: {e}",
        )

    if df.empty:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Uploaded file contains no data.",
        )

    log.info(f"[FileHandler] Parsed {len(df):,} rows, {len(df.columns)} columns")
    return df


def cleanup_upload(path: Path) -> None:
    """Remove uploaded file after processing (optional)."""
    try:
        path.unlink(missing_ok=True)
    except Exception:
        pass

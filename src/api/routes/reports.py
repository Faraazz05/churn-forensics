"""
api/routes/reports.py
=====================
GET /report/pdf   — generate + download executive PDF
GET /report/excel — generate + download Excel cohort report
"""
import asyncio
from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from core.security  import require_api_key
from services.report_service import generate_excel_report, generate_pdf_report
from utils.logger   import log

router = APIRouter()


@router.get("/report/excel", tags=["Reports"])
async def download_excel(_=Depends(require_api_key)):
    """Generate and download Excel cohort + segment report."""
    path = await asyncio.to_thread(generate_excel_report)
    suffix = path.suffix.lower()
    media  = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" \
             if suffix == ".xlsx" else "text/csv"
    return FileResponse(str(path), media_type=media,
                        filename=f"cohort_report{suffix}")


@router.get("/report/pdf", tags=["Reports"])
async def download_pdf(_=Depends(require_api_key)):
    """Generate and download executive PDF report."""
    path = await asyncio.to_thread(generate_pdf_report)
    suffix = path.suffix.lower()
    media  = "application/pdf" if suffix == ".pdf" else "text/plain"
    return FileResponse(str(path), media_type=media,
                        filename=f"executive_report{suffix}")

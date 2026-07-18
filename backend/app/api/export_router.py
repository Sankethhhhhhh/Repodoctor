from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from app.core.database import get_db
from app.export.csv_export import generate_csv
from app.export.html import generate_html
from app.export.markdown import generate_markdown
from app.export.pdf_export import generate_pdf
from app.export.sarif import generate_sarif
from app.repositories.report_repo import ReportRepository

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.models.models import Report

logger = logging.getLogger(__name__)

export_router = APIRouter(prefix="/reports", tags=["reports", "export"])


async def _get_report_or_404(report_id: str, db: AsyncSession = Depends(get_db)) -> Report:
    report_repo = ReportRepository(db)
    report = await report_repo.get_by_id(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@export_router.get("/{report_id}/export/md")
async def export_markdown(report_id: str, report: Report = Depends(_get_report_or_404)) -> Response:
    content = generate_markdown(report)
    return Response(
        content=content,
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="report-{report_id}.md"'},
    )


@export_router.get("/{report_id}/export/html")
async def export_html_endpoint(report_id: str, report: Report = Depends(_get_report_or_404)) -> Response:
    content = generate_html(report)
    return Response(
        content=content,
        media_type="text/html",
        headers={"Content-Disposition": f'attachment; filename="report-{report_id}.html"'},
    )


@export_router.get("/{report_id}/export/csv")
async def export_csv(report_id: str, report: Report = Depends(_get_report_or_404)) -> Response:
    content = generate_csv(report)
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="report-{report_id}.csv"'},
    )


@export_router.get("/{report_id}/export/pdf")
async def export_pdf(report_id: str, report: Report = Depends(_get_report_or_404)) -> Response:
    content = generate_pdf(report)
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="report-{report_id}.pdf"'},
    )


@export_router.get("/{report_id}/export/sarif")
async def export_sarif(report_id: str, report: Report = Depends(_get_report_or_404)) -> Response:
    content = generate_sarif(report)
    return Response(
        content=content,
        media_type="application/sarif+json",
        headers={"Content-Disposition": f'attachment; filename="report-{report_id}.sarif"'},
    )

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.database import get_db
from app.repositories.report_repo import ReportRepository

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

remediation_router = APIRouter(prefix="/reports", tags=["remediation"])


class RemediationResponse(BaseModel):
    remediations: list[dict[str, Any]]
    message: str = ""
    raw_response: str = ""
    error: str = ""


class NoRemediationResponse(BaseModel):
    message: str


@remediation_router.get(
    "/{report_id}/remediate",
    response_model=RemediationResponse | NoRemediationResponse,
)
async def get_remediation(
    report_id: str,
    db: AsyncSession = Depends(get_db),
) -> RemediationResponse | NoRemediationResponse:
    from app.ai.remediation import generate_remediation

    report_repo = ReportRepository(db)
    report = await report_repo.get_by_id(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    rules_data = json.loads(report.rules) if report.rules else []
    failed_rules = [r for r in rules_data if not r.get("passed", True)]
    if not failed_rules:
        return NoRemediationResponse(message="All rules passed — no remediation needed.")

    result = await generate_remediation(report)
    remediations = result.get("remediations", [])
    message = str(result.get("message", ""))
    raw_response = str(result.get("raw_response", ""))
    error = str(result.get("error", ""))
    return RemediationResponse(
        remediations=remediations if isinstance(remediations, list) else [],
        message=message,
        raw_response=raw_response,
        error=error,
    )

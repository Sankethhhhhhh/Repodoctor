from __future__ import annotations

import json
import logging
import time
from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from app.api.report_service import ReportService, deduplicate_recommendations
from app.api.schemas import (
    AnalyzeRequest,
    CategoryScore,
    DebugInfo,
    ReportListItem,
    ReportListResponse,
    ReportResponse,
    ReportSummary,
    StructuredRuleResult,
)
from app.core.database import get_db
from app.github.client import GitHubError, GitHubNotFoundError, GitHubRateLimitError
from app.github.service import GitHubService, parse_repo_url
from app.models.models import Report as ReportModel
from app.repositories.report_repo import ReportRepository

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

reports_router = APIRouter(prefix="/reports", tags=["reports"])


def _get_report_service(
    db: AsyncSession = Depends(get_db),
) -> ReportService:
    github_service = GitHubService()
    report_repo = ReportRepository(db)
    return ReportService(github_service=github_service, report_repo=report_repo)


def _build_report_response(report: object) -> ReportResponse:
    from app.models.models import Report as ReportModel

    assert isinstance(report, ReportModel)
    categories_data = json.loads(report.category_breakdown) if report.category_breakdown else []
    rules_data = json.loads(report.rules) if report.rules else []
    recommendations_raw = json.loads(report.recommendations) if report.recommendations else []

    categories = []
    for c in categories_data:
        details = c.get("details", [])
        structured_details = []
        for d in details:
            if isinstance(d, dict):
                structured_details.append(StructuredRuleResult(**d))
            else:
                structured_details.append(
                    StructuredRuleResult(
                        rule="unknown",
                        status="PASS" if "PASS" in str(d) else "FAIL",
                        evidence=str(d),
                    )
                )
        categories.append(
            CategoryScore(
                name=c["name"],
                score=c["score"],
                max_score=c["max_score"],
                details=structured_details,
            )
        )

    total_rules = len(rules_data)
    passed_rules = sum(1 for r in rules_data if r.get("passed", False))
    failed_rules = total_rules - passed_rules
    overall_percentage = report.score

    categories_passed = 0
    categories_failed = 0
    for cat in categories:
        if cat.max_score > 0:
            ratio = cat.score / cat.max_score
            if ratio >= 0.5:
                categories_passed += 1
            else:
                categories_failed += 1

    summary = ReportSummary(
        overall_percentage=overall_percentage,
        grade=report.grade,
        passed_rules=passed_rules,
        failed_rules=failed_rules,
        total_rules=total_rules,
        categories_passed=categories_passed,
        categories_failed=categories_failed,
    )

    recommendations = []
    if isinstance(recommendations_raw, list):
        for r in recommendations_raw:
            if isinstance(r, dict):
                recommendations.append(r.get("message", r.get("recommendation", "")))
            elif isinstance(r, str):
                recommendations.append(r)
    recommendations = deduplicate_recommendations(recommendations)

    repo_url = (
        report.repo_url
        if hasattr(report, "repo_url") and report.repo_url
        else f"https://github.com/{report.repo_full_name}"
    )

    return ReportResponse(
        id=str(report.id),
        repo_name=report.repo_full_name,
        repo_url=repo_url,
        owner=report.repo_full_name.split("/")[0] if "/" in report.repo_full_name else "",
        score=report.score,
        grade=report.grade,
        summary=summary,
        categories=categories,
        recommendations=recommendations,
        created_at=str(report.created_at),
    )


@reports_router.post(
    "",
    response_model=ReportResponse,
)
async def analyze_repo(
    request: AnalyzeRequest,
    service: ReportService = Depends(_get_report_service),
) -> ReportResponse:
    try:
        owner, repo = parse_repo_url(request.url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    logger.info("Analysis requested for %s/%s", owner, repo)
    start = time.monotonic()

    try:
        report = await service.analyze(request.url)
    except GitHubRateLimitError as e:
        logger.error("GitHub rate limit exceeded for %s/%s: %s", owner, repo, e.message)
        raise HTTPException(
            status_code=502,
            detail=f"GitHub API rate limit exceeded. {e.message}",
        ) from e
    except GitHubNotFoundError as e:
        logger.error("Repository not found: %s/%s: %s", owner, repo, e.message)
        raise HTTPException(
            status_code=404,
            detail=f"Repository not found: {owner}/{repo}",
        ) from e
    except GitHubError as e:
        logger.error("GitHub API error for %s/%s (status=%s): %s", owner, repo, e.status_code, e.message)
        raise HTTPException(
            status_code=502,
            detail=f"GitHub API error: {e.message}",
        ) from e
    except Exception as e:
        logger.exception("Analysis failed for %s/%s", owner, repo)
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {type(e).__name__}: {e}",
        ) from e

    elapsed = time.monotonic() - start
    logger.info("Analysis completed for %s/%s in %.1fs (score=%s, grade=%s)", owner, repo, elapsed, report.score, report.grade)
    return _build_report_response(report)


@reports_router.get(
    "",
    response_model=ReportListResponse,
)
async def list_reports(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
) -> ReportListResponse:
    report_repo = ReportRepository(db)
    reports = await report_repo.list_reports(skip=skip, limit=limit)

    summaries = [
        ReportListItem(
            id=str(r.id),
            repo_name=r.repo_full_name,
            repo_url=r.repo_url if hasattr(r, "repo_url") and r.repo_url else f"https://github.com/{r.repo_full_name}",
            score=r.score,
            grade=r.grade,
            created_at=str(r.created_at),
        )
        for r in reports
    ]

    return ReportListResponse(reports=summaries, total=len(summaries))


@reports_router.get(
    "/{report_id}",
    response_model=ReportResponse,
)
async def get_report(
    report_id: str,
    debug: bool = False,
    db: AsyncSession = Depends(get_db),
) -> ReportResponse:
    report_repo = ReportRepository(db)
    report = await report_repo.get_by_id(report_id)

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    response = _build_report_response(report)

    if debug:
        rules_data = json.loads(report.rules) if report.rules else []
        categories_data = json.loads(report.category_breakdown) if report.category_breakdown else []
        files_count = sum(len(c.get("details", [])) for c in categories_data)

        scoring_details = []
        for cat in categories_data:
            for detail in cat.get("details", []):
                scoring_details.append({
                    "rule": detail.get("rule", ""),
                    "status": detail.get("status", ""),
                    "points": detail.get("points", 0),
                    "max_points": detail.get("max_points", 0),
                    "evidence": detail.get("evidence", ""),
                    "severity": detail.get("severity", ""),
                })

        response.debug = DebugInfo(
            rules_evaluated=len(rules_data),
            github_files_inspected=files_count,
            github_api_calls=["GET /repos/{owner}/{repo}", "GET /repos/{owner}/{repo}/readme", "GET /repos/{owner}/{repo}/git/trees/{sha}", "GET /repos/{owner}/{repo}/commits", "GET /repos/{owner}/{repo}/actions/workflows", "GET /repos/{owner}/{repo}/license", "GET /repos/{owner}/{repo}/releases"],
            scoring_details=scoring_details,
            repo_metadata={
                "repo_name": report.repo_full_name,
                "commit_sha": report.commit_sha,
                "score": report.score,
                "grade": report.grade,
            },
        )

    return response


class HistoryItem(BaseModel):
    id: str
    repo_name: str
    score: float
    grade: str
    commit_sha: str
    created_at: str


class HistoryResponse(BaseModel):
    repo_full_name: str
    reports: list[HistoryItem]
    total: int


class TrendPoint(BaseModel):
    score: float
    grade: str
    commit_sha: str
    created_at: str


class TrendsResponse(BaseModel):
    repo_full_name: str
    data_points: list[TrendPoint]
    score_change: float | None
    grade_change: str | None


@reports_router.get(
    "/history/{owner}/{repo}",
    response_model=HistoryResponse,
    tags=["history"],
)
async def get_repo_history(
    owner: str,
    repo: str,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
) -> HistoryResponse:
    repo_full_name = f"{owner}/{repo}"
    result = await db.execute(
        select(ReportModel)
        .where(ReportModel.repo_full_name == repo_full_name)
        .order_by(ReportModel.created_at.desc())
        .limit(limit)
    )
    reports = list(result.scalars().all())

    return HistoryResponse(
        repo_full_name=repo_full_name,
        reports=[
            HistoryItem(
                id=str(r.id),
                repo_name=r.repo_full_name,
                score=r.score,
                grade=r.grade,
                commit_sha=r.commit_sha,
                created_at=str(r.created_at),
            )
            for r in reports
        ],
        total=len(reports),
    )


@reports_router.get(
    "/trends/{owner}/{repo}",
    response_model=TrendsResponse,
    tags=["trends"],
)
async def get_repo_trends(
    owner: str,
    repo: str,
    limit: int = 30,
    db: AsyncSession = Depends(get_db),
) -> TrendsResponse:
    repo_full_name = f"{owner}/{repo}"
    result = await db.execute(
        select(ReportModel)
        .where(ReportModel.repo_full_name == repo_full_name)
        .order_by(ReportModel.created_at.asc())
        .limit(limit)
    )
    reports = list(result.scalars().all())

    score_change = None
    grade_change = None
    if len(reports) >= 2:
        score_change = reports[-1].score - reports[0].score
        grade_change = f"{reports[0].grade} -> {reports[-1].grade}"

    return TrendsResponse(
        repo_full_name=repo_full_name,
        data_points=[
            TrendPoint(
                score=r.score,
                grade=r.grade,
                commit_sha=r.commit_sha,
                created_at=str(r.created_at),
            )
            for r in reports
        ],
        score_change=score_change,
        grade_change=grade_change,
    )

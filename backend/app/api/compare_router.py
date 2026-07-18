from __future__ import annotations

import json
from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.repositories.report_repo import ReportRepository

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

compare_router = APIRouter(prefix="/compare", tags=["compare"])


class CompareRequest(BaseModel):
    report_id_a: str = Field(..., description="First report ID")
    report_id_b: str = Field(..., description="Second report ID")


class CategoryComparison(BaseModel):
    name: str
    score_a: float
    score_b: float
    max_score: float
    winner: str


class CompareResponse(BaseModel):
    report_a: dict
    report_b: dict
    overall_winner: str
    score_difference: float
    category_comparison: list[CategoryComparison]
    improvement_suggestions: list[str]


def _get_simple_report(report: object) -> dict:
    from app.models.models import Report as ReportModel

    assert isinstance(report, ReportModel)
    cats = json.loads(report.category_breakdown) if report.category_breakdown else []
    return {
        "id": str(report.id),
        "repo_name": report.repo_full_name,
        "score": report.score,
        "grade": report.grade,
        "categories": [{"name": c["name"], "score": c["score"], "max_score": c["max_score"]} for c in cats],
    }


def _generate_suggestions(cat_comparison: list[CategoryComparison]) -> list[str]:
    suggestions = []
    for cat in cat_comparison:
        if cat.winner == "A" and cat.score_a < cat.score_b:
            pct = round((cat.score_a / cat.max_score) * 100) if cat.max_score > 0 else 0
            suggestions.append(
                f"Repository A scored {pct}% in {cat.name} — "
                f"improve to match Repository B's {round((cat.score_b / cat.max_score) * 100)}%"
            )
        elif cat.winner == "B" and cat.score_b < cat.score_a:
            pct = round((cat.score_b / cat.max_score) * 100) if cat.max_score > 0 else 0
            suggestions.append(
                f"Repository B scored {pct}% in {cat.name} — "
                f"improve to match Repository A's {round((cat.score_a / cat.max_score) * 100)}%"
            )

    if not suggestions:
        suggestions.append("Both repositories are performing well across all categories!")

    return suggestions


@compare_router.post("", response_model=CompareResponse)
async def compare_reports(
    request: CompareRequest,
    db: AsyncSession = Depends(get_db),
) -> CompareResponse:
    report_repo = ReportRepository(db)
    report_a = await report_repo.get_by_id(request.report_id_a)
    report_b = await report_repo.get_by_id(request.report_id_b)

    if not report_a:
        raise HTTPException(status_code=404, detail=f"Report {request.report_id_a} not found")
    if not report_b:
        raise HTTPException(status_code=404, detail=f"Report {request.report_id_b} not found")

    simple_a = _get_simple_report(report_a)
    simple_b = _get_simple_report(report_b)

    winner = "A" if simple_a["score"] > simple_b["score"] else ("B" if simple_b["score"] > simple_a["score"] else "Tie")

    categories_a = {c["name"]: c for c in simple_a["categories"]}
    categories_b = {c["name"]: c for c in simple_b["categories"]}
    all_names = list(dict.fromkeys(list(categories_a.keys()) + list(categories_b.keys())))

    cat_comparison = []
    for name in all_names:
        ca = categories_a.get(name, {"score": 0, "max_score": 0})
        cb = categories_b.get(name, {"score": 0, "max_score": 0})
        cat_winner = "A" if ca["score"] > cb["score"] else ("B" if cb["score"] > ca["score"] else "Tie")
        cat_comparison.append(
            CategoryComparison(
                name=name,
                score_a=ca["score"],
                score_b=cb["score"],
                max_score=max(ca["max_score"], cb["max_score"]),
                winner=cat_winner,
            )
        )

    suggestions = _generate_suggestions(cat_comparison)

    return CompareResponse(
        report_a=simple_a,
        report_b=simple_b,
        overall_winner=winner,
        score_difference=abs(simple_a["score"] - simple_b["score"]),
        category_comparison=cat_comparison,
        improvement_suggestions=suggestions,
    )

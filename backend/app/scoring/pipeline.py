from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.scoring.cicd import CI_CD_RULES
from app.scoring.documentation import DOCUMENTATION_RULES
from app.scoring.git_hygiene import GIT_HYGIENE_RULES
from app.scoring.licensing import LICENSING_RULES
from app.scoring.rule import Category, Rule, RuleResult
from app.scoring.security import SECURITY_RULES
from app.scoring.testing import TESTING_RULES

if TYPE_CHECKING:
    from app.github.schemas import GitHubRepositoryData

ALL_RULES: list[Rule] = (
    DOCUMENTATION_RULES + TESTING_RULES + CI_CD_RULES + GIT_HYGIENE_RULES + LICENSING_RULES + SECURITY_RULES
)

CATEGORY_WEIGHTS: dict[Category, int] = {
    Category.DOCUMENTATION: 20,
    Category.TESTING: 13,
    Category.CI_CD: 13,
    Category.GIT_HYGIENE: 23,
    Category.LICENSING: 7,
    Category.SECURITY: 24,
}


class CategoryScore:
    def __init__(
        self,
        name: str,
        score: int,
        max_score: int,
        details: list[dict[str, Any]] | None = None,
    ) -> None:
        self.name = name
        self.score = score
        self.max_score = max_score
        self.details = details or []

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "score": self.score,
            "max_score": self.max_score,
            "details": self.details,
        }


class ScoringResult:
    def __init__(
        self,
        overall_score: int,
        grade: str,
        categories: list[CategoryScore],
        rules: list[RuleResult],
    ) -> None:
        self.overall_score = overall_score
        self.grade = grade
        self.categories = categories
        self.rules = rules

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": self.overall_score,
            "grade": self.grade,
            "categories": [c.to_dict() for c in self.categories],
            "rules": [r.to_dict() for r in self.rules],
        }


def calculate_grade(score: int) -> str:
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 60:
        return "D"
    return "F"


def run_scoring(data: GitHubRepositoryData) -> ScoringResult:
    rule_results: list[RuleResult] = []
    for rule in ALL_RULES:
        result = rule.evaluate(data)
        rule_results.append(result)

    category_scores: dict[Category, dict[str, int]] = {}
    for cat in Category:
        category_scores[cat] = {"earned": 0, "max": 0}

    for result in rule_results:
        cat = result.category
        category_scores[cat]["max"] += result.weight
        if result.passed:
            category_scores[cat]["earned"] += result.weight

    total_earned = 0
    total_max = 0
    categories: list[CategoryScore] = []

    rules_by_category: dict[Category, list[dict[str, object]]] = {cat: [] for cat in Category}
    for result in rule_results:
        status = "PASS" if result.passed else "FAIL"
        finding: dict[str, object] = {
            "rule": result.rule_id,
            "status": status,
            "severity": result.severity,
            "evidence": result.evidence,
            "recommendation": result.recommendation or "",
            "documentation": result.documentation,
            "points": result.weight if result.passed else 0,
            "max_points": result.weight,
        }
        rules_by_category[result.category].append(finding)

    for cat in Category:
        cat_weight = CATEGORY_WEIGHTS[cat]
        cat_data = category_scores[cat]

        cat_ratio = cat_data["earned"] / cat_data["max"] if cat_data["max"] > 0 else 0.0

        cat_score = round(cat_ratio * cat_weight)
        total_earned += cat_score
        total_max += cat_weight

        categories.append(
            CategoryScore(
                name=cat.value,
                score=cat_score,
                max_score=cat_weight,
                details=rules_by_category[cat],
            )
        )

    overall = round((total_earned / total_max) * 100) if total_max > 0 else 0
    grade = calculate_grade(overall)

    return ScoringResult(
        overall_score=overall,
        grade=grade,
        categories=categories,
        rules=rule_results,
    )

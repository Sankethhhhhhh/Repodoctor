from __future__ import annotations

from abc import ABC, abstractmethod
from enum import StrEnum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.github.schemas import GitHubRepositoryData


class Category(StrEnum):
    TESTING = "Testing"
    CI_CD = "CI/CD"
    DOCUMENTATION = "Documentation"
    GIT_HYGIENE = "Git Hygiene"
    LICENSING = "Licensing"
    SECURITY = "Security"


class RuleResult:
    def __init__(
        self,
        rule_id: str,
        category: Category,
        passed: bool,
        weight: int,
        evidence: str,
        recommendation: str | None = None,
        severity: str = "medium",
        documentation: str | None = None,
    ) -> None:
        self.rule_id = rule_id
        self.category = category
        self.passed = passed
        self.weight = weight
        self.evidence = evidence
        self.recommendation = recommendation
        self.severity = severity
        self.documentation = documentation

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.rule_id,
            "category": self.category.value,
            "passed": self.passed,
            "weight": self.weight,
            "evidence": self.evidence,
            "recommendation": self.recommendation,
            "severity": self.severity,
            "documentation": self.documentation,
        }


class Rule(ABC):
    @property
    @abstractmethod
    def rule_id(self) -> str: ...

    @property
    @abstractmethod
    def category(self) -> Category: ...

    @property
    @abstractmethod
    def weight(self) -> int: ...

    @property
    @abstractmethod
    def description(self) -> str: ...

    @property
    def severity(self) -> str:
        return "medium"

    @property
    def documentation(self) -> str | None:
        return None

    @abstractmethod
    def evaluate(self, data: GitHubRepositoryData) -> RuleResult: ...

    def _pass(self, evidence: str) -> RuleResult:
        return RuleResult(
            rule_id=self.rule_id,
            category=self.category,
            passed=True,
            weight=self.weight,
            evidence=evidence,
            severity=self.severity,
            documentation=self.documentation,
        )

    def _fail(
        self,
        evidence: str,
        recommendation: str | None = None,
    ) -> RuleResult:
        return RuleResult(
            rule_id=self.rule_id,
            category=self.category,
            passed=False,
            weight=self.weight,
            evidence=evidence,
            recommendation=recommendation,
            severity=self.severity,
            documentation=self.documentation,
        )

    @staticmethod
    def _file_exists(file_paths: set[str], target: str) -> str | None:
        target_lower = target.lower()
        for path in file_paths:
            if path.lower() == target_lower:
                return path
        return None

    @staticmethod
    def _file_matches(file_paths: set[str], targets: list[str]) -> str | None:
        for t in targets:
            hit = Rule._file_exists(file_paths, t)
            if hit:
                return hit
        return None

    @staticmethod
    def _dir_exists(tree_dirs: set[str], target: str) -> bool:
        target_lower = target.lower().rstrip("/")
        return any(d.lower().rstrip("/") == target_lower for d in tree_dirs)

    @staticmethod
    def _has_file_under(file_paths: set[str], prefix: str) -> str | None:
        prefix_lower = prefix.lower().rstrip("/")
        for path in file_paths:
            if path.lower().startswith(prefix_lower + "/") or path.lower().startswith(prefix_lower):
                return path
        return None

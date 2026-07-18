from __future__ import annotations

from pydantic import BaseModel, Field, computed_field


class AnalyzeRequest(BaseModel):
    url: str = Field(
        ...,
        description="GitHub repository URL",
        examples=["https://github.com/owner/repo"],
    )


class StructuredRuleResult(BaseModel):
    rule: str = Field(..., description="Rule identifier")
    status: str = Field(..., description="PASS or FAIL")
    severity: str = Field(default="medium", description="low, medium, high, or info")
    evidence: str = Field(..., description="Evidence for the rule evaluation result")
    recommendation: str = Field(default="", description="Recommendation if rule failed")
    documentation: str | None = Field(default=None, description="Optional documentation URL")
    points: int = Field(default=0, description="Points awarded for this rule")
    max_points: int = Field(default=0, description="Maximum possible points for this rule")


class CategoryScore(BaseModel):
    name: str
    score: float
    max_score: float
    details: list[StructuredRuleResult] = Field(default_factory=list)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def percentage(self) -> float:
        if self.max_score <= 0:
            return 0.0
        return round(self.score / self.max_score * 100, 1)


class ReportSummary(BaseModel):
    overall_percentage: int
    grade: str
    passed_rules: int
    failed_rules: int
    total_rules: int
    categories_passed: int
    categories_failed: int


class DebugInfo(BaseModel):
    rules_evaluated: int = Field(description="Total number of rules evaluated")
    github_files_inspected: int = Field(description="Number of files in the repository tree")
    github_api_calls: list[str] = Field(default_factory=list, description="GitHub API endpoints called")
    scoring_details: list[dict] = Field(default_factory=list, description="Per-rule scoring details with points")
    repo_metadata: dict = Field(default_factory=dict, description="Repository metadata used in analysis")


class ReportResponse(BaseModel):
    id: str
    repo_name: str
    repo_url: str
    owner: str
    score: float
    grade: str
    summary: ReportSummary
    categories: list[CategoryScore]
    recommendations: list[str]
    created_at: str
    debug: DebugInfo | None = None


class ReportListItem(BaseModel):
    id: str
    repo_name: str
    repo_url: str
    score: float
    grade: str
    created_at: str


class ReportListResponse(BaseModel):
    reports: list[ReportListItem]
    total: int


class ErrorResponse(BaseModel):
    error: dict[str, str]

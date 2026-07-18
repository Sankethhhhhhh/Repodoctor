"""Regression tests to prevent schema drift between the scoring pipeline and the API models."""

import json

from app.api.schemas import CategoryScore as PydanticCategoryScore
from app.api.schemas import ReportResponse, ReportSummary, StructuredRuleResult
from app.github.schemas import (
    CommitInfo,
    GitHubRepositoryData,
    RepositoryInfo,
)
from app.scoring.pipeline import CategoryScore as PipelineCategoryScore
from app.scoring.pipeline import run_scoring

DEFAULT_README = "# Test\n\n## Installation\n\npip install test\n\n## Usage\n\nimport test\n\n## License\n\nMIT"


def _make_repo(**kwargs: object) -> GitHubRepositoryData:
    defaults: dict[str, object] = {
        "repo": RepositoryInfo(
            full_name="test/repo",
            name="repo",
            owner="test",
            description="Test repo",
            default_branch="main",
            created_at="2026-01-01T00:00:00Z",
            updated_at="2026-07-01T00:00:00Z",
            pushed_at="2026-07-01T00:00:00Z",
            stargazers_count=100,
            forks_count=20,
            open_issues_count=5,
            language="Python",
            topics=[],
        ),
        "readme": DEFAULT_README,
        "tree": [],
        "commits": [
            CommitInfo(
                sha="abc123",
                message="Add initial implementation",
                author_name="Alice",
                author_email="alice@test.com",
                author_date="2026-01-01T00:00:00Z",
                committer_name="Alice",
                committer_date="2026-01-01T00:00:00Z",
            ),
        ],
        "workflows": [],
        "license": None,
        "has_gitignore": False,
        "has_dockerfile": False,
    }
    defaults.update(kwargs)
    return GitHubRepositoryData(**defaults)  # type: ignore[arg-type]


class TestPipelineCategoryScoreDict:
    """Verify that the pipeline CategoryScore.to_dict() output is compatible
    with the Pydantic CategoryScore model."""

    def test_to_dict_includes_required_fields(self) -> None:
        cs = PipelineCategoryScore(name="Testing", score=8, max_score=10)
        d = cs.to_dict()
        assert "name" in d
        assert "score" in d
        assert "max_score" in d
        assert "details" in d

    def test_to_dict_details_default_empty(self) -> None:
        cs = PipelineCategoryScore(name="Testing", score=8, max_score=10)
        d = cs.to_dict()
        assert d["details"] == []

    def test_to_dict_details_populated(self) -> None:
        details = [
            {
                "rule": "README_EXISTS",
                "status": "PASS",
                "severity": "medium",
                "evidence": "README found",
                "recommendation": "",
                "documentation": None,
            },
            {
                "rule": "TEST_DIRECTORY",
                "status": "FAIL",
                "severity": "medium",
                "evidence": "No tests",
                "recommendation": "Add unit tests",
                "documentation": None,
            },
        ]
        cs = PipelineCategoryScore(name="Testing", score=8, max_score=10, details=details)
        d = cs.to_dict()
        assert d["details"] == details


class TestPipelineOutputSchemaSync:
    """Verify that running the full pipeline produces category dicts that
    round-trip through the Pydantic schema without errors."""

    def test_round_trip_through_pydantic(self) -> None:
        data = _make_repo()
        result = run_scoring(data)

        for cat in result.categories:
            d = cat.to_dict()
            model = PydanticCategoryScore(**d)
            assert model.name == d["name"]
            assert model.score == d["score"]
            assert model.max_score == d["max_score"]
            assert isinstance(model.details, list)

    def test_json_round_trip(self) -> None:
        data = _make_repo()
        result = run_scoring(data)

        category_dicts = [c.to_dict() for c in result.categories]
        serialized = json.dumps(category_dicts)
        deserialized = json.loads(serialized)

        models = [PydanticCategoryScore(**d) for d in deserialized]
        assert len(models) == len(category_dicts)
        for model, original in zip(models, category_dicts, strict=True):
            assert model.name == original["name"]


class TestPydanticCategoryScore:
    """Verify the Pydantic CategoryScore model computes percentage correctly
    and accepts pipeline-produced dicts."""

    def test_construction_without_percentage(self) -> None:
        model = PydanticCategoryScore(name="Testing", score=15, max_score=20, details=[])
        assert model.percentage == 75.0

    def test_construction_without_details(self) -> None:
        model = PydanticCategoryScore(name="Testing", score=15, max_score=20)
        assert model.details == []

    def test_percentage_computed_correctly(self) -> None:
        model = PydanticCategoryScore(name="Testing", score=10, max_score=20)
        assert model.percentage == 50.0

    def test_percentage_zero_max_score(self) -> None:
        model = PydanticCategoryScore(name="Testing", score=0, max_score=0)
        assert model.percentage == 0.0

    def test_percentage_in_serialized_output(self) -> None:
        model = PydanticCategoryScore(
            name="Testing",
            score=15,
            max_score=20,
            details=[
                StructuredRuleResult(rule="README_EXISTS", status="PASS", evidence="ok"),
            ],
        )
        dumped = model.model_dump()
        assert "percentage" in dumped
        assert dumped["percentage"] == 75.0

    def test_json_serialization_includes_percentage(self) -> None:
        model = PydanticCategoryScore(name="Testing", score=15, max_score=20)
        j = model.model_dump_json()
        data = json.loads(j)
        assert data["percentage"] == 75.0


class TestStructuredRuleResult:
    """Verify the StructuredRuleResult model works correctly."""

    def test_minimal_construction(self) -> None:
        result = StructuredRuleResult(rule="README_EXISTS", status="PASS", evidence="README found")
        assert result.rule == "README_EXISTS"
        assert result.status == "PASS"
        assert result.severity == "medium"
        assert result.evidence == "README found"
        assert result.recommendation == ""
        assert result.documentation is None

    def test_full_construction(self) -> None:
        result = StructuredRuleResult(
            rule="SECRET_PATTERNS",
            status="FAIL",
            severity="high",
            evidence="Secrets found",
            recommendation="Remove secrets",
            documentation="https://docs.example.com",
        )
        assert result.severity == "high"
        assert result.documentation == "https://docs.example.com"

    def test_serialization(self) -> None:
        result = StructuredRuleResult(rule="TEST", status="PASS", evidence="ok")
        dumped = result.model_dump()
        assert dumped["rule"] == "TEST"
        assert dumped["status"] == "PASS"
        assert dumped["severity"] == "medium"


class TestReportSummary:
    """Verify the ReportSummary model."""

    def test_construction(self) -> None:
        summary = ReportSummary(
            overall_percentage=75,
            grade="C",
            passed_rules=15,
            failed_rules=7,
            total_rules=22,
            categories_passed=4,
            categories_failed=2,
        )
        assert summary.overall_percentage == 75
        assert summary.grade == "C"
        assert summary.total_rules == 22


class TestReportResponseSchema:
    """Verify ReportResponse can be constructed with pipeline-produced categories."""

    def test_report_response_accepts_pipeline_categories(self) -> None:
        data = _make_repo()
        result = run_scoring(data)

        categories = [PydanticCategoryScore(**c.to_dict()) for c in result.categories]
        summary = ReportSummary(
            overall_percentage=result.overall_score,
            grade=result.grade,
            passed_rules=sum(1 for r in result.rules if r.passed),
            failed_rules=sum(1 for r in result.rules if not r.passed),
            total_rules=len(result.rules),
            categories_passed=4,
            categories_failed=2,
        )
        response = ReportResponse(
            id="test-id",
            repo_name="test/repo",
            repo_url="https://github.com/test/repo",
            owner="test",
            score=result.overall_score,
            grade=result.grade,
            summary=summary,
            categories=categories,
            recommendations=["Add tests"],
            created_at="2026-01-01",
        )
        dumped = response.model_dump()
        assert "percentage" in dumped["categories"][0]
        assert isinstance(dumped["categories"][0]["details"], list)
        assert "summary" in dumped
        assert dumped["summary"]["overall_percentage"] == result.overall_score

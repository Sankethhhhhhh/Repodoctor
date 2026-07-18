import json

from app.api.schemas import StructuredRuleResult
from app.github.schemas import (
    GitHubRepositoryData,
    RepositoryInfo,
)
from app.scoring.pipeline import run_scoring


def _make_data(**kwargs: object) -> GitHubRepositoryData:
    defaults: dict[str, object] = {
        "repo": RepositoryInfo(
            full_name="test/repo",
            name="repo",
            owner="test",
            description="Test",
            default_branch="main",
            created_at="2026-01-01T00:00:00Z",
            updated_at="2026-07-01T00:00:00Z",
            pushed_at="2026-07-01T00:00:00Z",
            stargazers_count=0,
            forks_count=0,
            open_issues_count=0,
            language=None,
            topics=[],
        ),
        "readme": None,
        "tree": [],
        "commits": [],
        "workflows": [],
        "license": None,
        "has_gitignore": False,
        "has_dockerfile": False,
    }
    defaults.update(kwargs)
    return GitHubRepositoryData(**defaults)  # type: ignore[arg-type]


class TestStructuredRuleSerialization:
    def test_pipeline_produces_structured_details(self) -> None:
        data = _make_data()
        result = run_scoring(data)

        for cat in result.categories:
            d = cat.to_dict()
            for detail in d["details"]:
                assert isinstance(detail, dict)
                assert "rule" in detail
                assert "status" in detail
                assert "severity" in detail
                assert "evidence" in detail
                assert "recommendation" in detail
                assert "documentation" in detail

    def test_structured_details_have_valid_status(self) -> None:
        data = _make_data()
        result = run_scoring(data)

        for cat in result.categories:
            for detail in cat.details:
                assert detail["status"] in ("PASS", "FAIL")

    def test_structured_details_have_valid_severity(self) -> None:
        data = _make_data()
        result = run_scoring(data)

        valid_severities = {"low", "medium", "high", "info"}
        for cat in result.categories:
            for detail in cat.details:
                assert detail["severity"] in valid_severities

    def test_structured_details_roundtrip_json(self) -> None:
        data = _make_data()
        result = run_scoring(data)

        for cat in result.categories:
            serialized = json.dumps(cat.details)
            deserialized = json.loads(serialized)
            assert len(deserialized) == len(cat.details)
            for d in deserialized:
                assert isinstance(d, dict)

    def test_structured_details_into_pydantic(self) -> None:
        data = _make_data()
        result = run_scoring(data)

        for cat in result.categories:
            pydantic_details = [StructuredRuleResult(**d) for d in cat.details]
            assert len(pydantic_details) == len(cat.details)

    def test_security_rules_have_severity(self) -> None:
        data = _make_data()
        result = run_scoring(data)

        security_cat = None
        for cat in result.categories:
            if cat.name == "Security":
                security_cat = cat
                break

        assert security_cat is not None
        for detail in security_cat.details:
            assert detail["severity"] in ("high", "medium", "info")

    def test_failed_rules_have_recommendations(self) -> None:
        data = _make_data()
        result = run_scoring(data)

        for cat in result.categories:
            for detail in cat.details:
                if detail["status"] == "FAIL" and detail["rule"] not in ("DEPENDABOT", "SECURITY_POLICY"):
                    assert detail["recommendation"], f"Rule {detail['rule']} failed but has no recommendation"

    def test_all_rules_present_in_details(self) -> None:
        data = _make_data()
        result = run_scoring(data)

        all_rule_ids = {r.rule_id for r in result.rules}
        details_rule_ids = set()
        for cat in result.categories:
            for detail in cat.details:
                details_rule_ids.add(detail["rule"])

        assert all_rule_ids == details_rule_ids

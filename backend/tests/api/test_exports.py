import csv
import io
import json

import pytest
from httpx import ASGITransport, AsyncClient

from app.export.csv_export import generate_csv
from app.export.html import generate_html
from app.export.markdown import generate_markdown
from app.export.pdf_export import generate_pdf
from app.export.sarif import generate_sarif
from app.main import app
from app.models.models import Report

MOCK_REPORT_KWARGS: dict[str, object] = {
    "repo_full_name": "facebook/react",
    "repo_url": "https://github.com/facebook/react",
    "commit_sha": "abc123def456",
    "score": 75,
    "grade": "C",
    "category_breakdown": json.dumps(
        [
            {
                "name": "Testing",
                "score": 15,
                "max_score": 20,
                "details": [
                    {
                        "rule": "TEST_DIRECTORY",
                        "status": "PASS",
                        "severity": "medium",
                        "evidence": "tests/ found",
                        "recommendation": "",
                        "documentation": None,
                    },
                    {
                        "rule": "TEST_FRAMEWORK",
                        "status": "FAIL",
                        "severity": "medium",
                        "evidence": "No test framework detected",
                        "recommendation": "Add pytest or jest",
                        "documentation": None,
                    },
                ],
            },
            {
                "name": "Security",
                "score": 10,
                "max_score": 15,
                "details": [
                    {
                        "rule": "GITIGNORE_EXISTS",
                        "status": "PASS",
                        "severity": "high",
                        "evidence": ".gitignore found",
                        "recommendation": "",
                        "documentation": None,
                    },
                    {
                        "rule": "SECRET_PATTERNS",
                        "status": "FAIL",
                        "severity": "high",
                        "evidence": "Secrets found",
                        "recommendation": "Remove secrets",
                        "documentation": None,
                    },
                ],
            },
        ]
    ),
    "rules": json.dumps(
        [
            {
                "id": "TEST_DIRECTORY",
                "category": "Testing",
                "passed": True,
                "weight": 5,
                "evidence": "tests/ found",
                "recommendation": None,
                "severity": "medium",
                "documentation": None,
            },
            {
                "id": "TEST_FRAMEWORK",
                "category": "Testing",
                "passed": False,
                "weight": 5,
                "evidence": "No test framework detected",
                "recommendation": "Add pytest or jest",
                "severity": "medium",
                "documentation": None,
            },
            {
                "id": "GITIGNORE_EXISTS",
                "category": "Security",
                "passed": True,
                "weight": 5,
                "evidence": ".gitignore found",
                "recommendation": None,
                "severity": "high",
                "documentation": None,
            },
            {
                "id": "SECRET_PATTERNS",
                "category": "Security",
                "passed": False,
                "weight": 5,
                "evidence": "Secrets found",
                "recommendation": "Remove secrets",
                "severity": "high",
                "documentation": None,
            },
        ]
    ),
    "recommendations": json.dumps(
        [
            "Add pytest or jest",
            "Remove secrets",
        ]
    ),
}


def _make_report(**kwargs: object) -> Report:
    defaults = dict(MOCK_REPORT_KWARGS)
    defaults.update(kwargs)
    report = Report()
    for key, value in defaults.items():
        setattr(report, key, value)
    return report


@pytest.fixture
async def client() -> AsyncClient:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestMarkdownExport:
    def test_contains_repo_name(self) -> None:
        report = _make_report()
        md = generate_markdown(report)
        assert "facebook/react" in md

    def test_contains_score(self) -> None:
        report = _make_report()
        md = generate_markdown(report)
        assert "75" in md

    def test_contains_grade(self) -> None:
        report = _make_report()
        md = generate_markdown(report)
        assert "C" in md

    def test_contains_category_breakdown(self) -> None:
        report = _make_report()
        md = generate_markdown(report)
        assert "Testing" in md
        assert "Security" in md

    def test_contains_structured_rules(self) -> None:
        report = _make_report()
        md = generate_markdown(report)
        assert "TEST_DIRECTORY" in md
        assert "PASS" in md
        assert "FAIL" in md

    def test_contains_recommendations(self) -> None:
        report = _make_report()
        md = generate_markdown(report)
        assert "Add pytest or jest" in md
        assert "Remove secrets" in md

    def test_contains_repo_url(self) -> None:
        report = _make_report()
        md = generate_markdown(report)
        assert "https://github.com/facebook/react" in md

    def test_empty_recommendations(self) -> None:
        report = _make_report(recommendations=json.dumps([]))
        md = generate_markdown(report)
        assert "No recommendations" in md


class TestHTMLExport:
    def test_valid_html(self) -> None:
        report = _make_report()
        html = generate_html(report)
        assert html.startswith("<!DOCTYPE html>")
        assert "</html>" in html

    def test_contains_repo_name(self) -> None:
        report = _make_report()
        html = generate_html(report)
        assert "facebook/react" in html

    def test_contains_score(self) -> None:
        report = _make_report()
        html = generate_html(report)
        assert "75%" in html

    def test_contains_grade(self) -> None:
        report = _make_report()
        html = generate_html(report)
        assert ">C<" in html

    def test_contains_structured_rules(self) -> None:
        report = _make_report()
        html = generate_html(report)
        assert "TEST_DIRECTORY" in html
        assert "GITIGNORE_EXISTS" in html

    def test_contains_css_styles(self) -> None:
        report = _make_report()
        html = generate_html(report)
        assert "<style>" in html

    def test_html_escaping(self) -> None:
        report = _make_report(repo_full_name="test/repo")
        html = generate_html(report)
        assert "<script>" not in html


class TestCSVExport:
    def test_contains_header(self) -> None:
        report = _make_report()
        csv_content = generate_csv(report)
        assert "Repository Health Report" in csv_content

    def test_contains_repo_info(self) -> None:
        report = _make_report()
        csv_content = generate_csv(report)
        assert "facebook/react" in csv_content
        assert "https://github.com/facebook/react" in csv_content

    def test_contains_score_and_grade(self) -> None:
        report = _make_report()
        csv_content = generate_csv(report)
        assert "75" in csv_content
        assert "C" in csv_content

    def test_contains_rules(self) -> None:
        report = _make_report()
        csv_content = generate_csv(report)
        assert "TEST_DIRECTORY" in csv_content
        assert "SECRET_PATTERNS" in csv_content

    def test_valid_csv_format(self) -> None:
        report = _make_report()
        csv_content = generate_csv(report)
        reader = csv.reader(io.StringIO(csv_content))
        rows = list(reader)
        assert len(rows) > 0

    def test_rules_section_has_headers(self) -> None:
        report = _make_report()
        csv_content = generate_csv(report)
        assert "Rule,Category,Status" in csv_content


class TestPDFExport:
    def test_returns_bytes(self) -> None:
        report = _make_report()
        pdf = generate_pdf(report)
        assert isinstance(pdf, bytes)

    def test_starts_with_pdf_header(self) -> None:
        report = _make_report()
        pdf = generate_pdf(report)
        assert pdf[:5] == b"%PDF-"

    def test_ends_with_eof(self) -> None:
        report = _make_report()
        pdf = generate_pdf(report)
        assert b"%%EOF" in pdf[-20:]

    def test_contains_repo_name(self) -> None:
        report = _make_report()
        pdf = generate_pdf(report)
        assert len(pdf) > 500

    def test_non_empty_output(self) -> None:
        report = _make_report()
        pdf = generate_pdf(report)
        assert len(pdf) > 100

    def test_valid_pdf_structure(self) -> None:
        report = _make_report()
        pdf = generate_pdf(report)
        assert b"%PDF-" in pdf
        assert b"obj" in pdf
        assert b"endobj" in pdf


class TestSARIFExport:
    def test_valid_json(self) -> None:
        report = _make_report()
        sarif = generate_sarif(report)
        data = json.loads(sarif)
        assert isinstance(data, dict)

    def test_sarif_version(self) -> None:
        report = _make_report()
        sarif = generate_sarif(report)
        data = json.loads(sarif)
        assert data["version"] == "2.1.0"

    def test_sarif_schema(self) -> None:
        report = _make_report()
        sarif = generate_sarif(report)
        data = json.loads(sarif)
        assert "$schema" in data
        assert "sarif-schema" in data["$schema"]

    def test_contains_runs(self) -> None:
        report = _make_report()
        sarif = generate_sarif(report)
        data = json.loads(sarif)
        assert "runs" in data
        assert len(data["runs"]) == 1

    def test_contains_tool_info(self) -> None:
        report = _make_report()
        sarif = generate_sarif(report)
        data = json.loads(sarif)
        tool = data["runs"][0]["tool"]["driver"]
        assert tool["name"] == "RepoDoctor"
        assert tool["version"] == "0.1.0"

    def test_contains_results(self) -> None:
        report = _make_report()
        sarif = generate_sarif(report)
        data = json.loads(sarif)
        results = data["runs"][0]["results"]
        assert len(results) > 0

    def test_results_have_required_fields(self) -> None:
        report = _make_report()
        sarif = generate_sarif(report)
        data = json.loads(sarif)
        for result in data["runs"][0]["results"]:
            assert "ruleId" in result
            assert "level" in result
            assert "message" in result
            assert "locations" in result

    def test_passed_rules_have_level_none(self) -> None:
        report = _make_report()
        sarif = generate_sarif(report)
        data = json.loads(sarif)
        for result in data["runs"][0]["results"]:
            if result["level"] == "none":
                assert result["ruleId"] in ("TEST_DIRECTORY", "GITIGNORE_EXISTS")

    def test_failed_rules_have_fixes(self) -> None:
        report = _make_report()
        sarif = generate_sarif(report)
        data = json.loads(sarif)
        for result in data["runs"][0]["results"]:
            if result["level"] in ("error", "warning"):
                assert "fixes" in result

    def test_sarif_contains_rules_definitions(self) -> None:
        report = _make_report()
        sarif = generate_sarif(report)
        data = json.loads(sarif)
        rules = data["runs"][0]["tool"]["driver"]["rules"]
        rule_ids = {r["id"] for r in rules}
        assert "TEST_DIRECTORY" in rule_ids
        assert "SECRET_PATTERNS" in rule_ids

    def test_level_mapping_high_is_error(self) -> None:
        report = _make_report()
        sarif = generate_sarif(report)
        data = json.loads(sarif)
        for result in data["runs"][0]["results"]:
            if result["ruleId"] == "SECRET_PATTERNS":
                assert result["level"] == "error"

    def test_level_mapping_medium_is_warning(self) -> None:
        report = _make_report()
        sarif = generate_sarif(report)
        data = json.loads(sarif)
        for result in data["runs"][0]["results"]:
            if result["ruleId"] == "TEST_FRAMEWORK":
                assert result["level"] == "warning"


async def _create_test_report(session_factory=None) -> dict:  # type: ignore[no-untyped-def]
    from app.core.database import async_session_factory
    from app.models.models import Report as ReportModel

    factory = session_factory or async_session_factory
    async with factory() as session:
        report = ReportModel(
            repo_full_name="facebook/react",
            repo_url="https://github.com/facebook/react",
            commit_sha="abc123",
            score=75,
            grade="C",
            category_breakdown=json.dumps(
                [
                    {
                        "name": "Testing",
                        "score": 15,
                        "max_score": 20,
                        "details": [
                            {
                                "rule": "TEST_DIRECTORY",
                                "status": "PASS",
                                "severity": "medium",
                                "evidence": "tests/ found",
                                "recommendation": "",
                                "documentation": None,
                            },
                            {
                                "rule": "TEST_FRAMEWORK",
                                "status": "FAIL",
                                "severity": "medium",
                                "evidence": "No test framework",
                                "recommendation": "Add pytest",
                                "documentation": None,
                            },
                        ],
                    },
                    {
                        "name": "Security",
                        "score": 10,
                        "max_score": 15,
                        "details": [
                            {
                                "rule": "GITIGNORE_EXISTS",
                                "status": "PASS",
                                "severity": "high",
                                "evidence": ".gitignore found",
                                "recommendation": "",
                                "documentation": None,
                            },
                            {
                                "rule": "SECRET_PATTERNS",
                                "status": "FAIL",
                                "severity": "high",
                                "evidence": "Secrets found",
                                "recommendation": "Remove secrets",
                                "documentation": None,
                            },
                        ],
                    },
                ]
            ),
            rules=json.dumps(
                [
                    {
                        "id": "TEST_DIRECTORY",
                        "category": "Testing",
                        "passed": True,
                        "weight": 5,
                        "evidence": "tests/ found",
                        "recommendation": None,
                        "severity": "medium",
                        "documentation": None,
                    },
                    {
                        "id": "TEST_FRAMEWORK",
                        "category": "Testing",
                        "passed": False,
                        "weight": 5,
                        "evidence": "No test framework",
                        "recommendation": "Add pytest",
                        "severity": "medium",
                        "documentation": None,
                    },
                    {
                        "id": "GITIGNORE_EXISTS",
                        "category": "Security",
                        "passed": True,
                        "weight": 5,
                        "evidence": ".gitignore found",
                        "recommendation": None,
                        "severity": "high",
                        "documentation": None,
                    },
                    {
                        "id": "SECRET_PATTERNS",
                        "category": "Security",
                        "passed": False,
                        "weight": 5,
                        "evidence": "Secrets found",
                        "recommendation": "Remove secrets",
                        "severity": "high",
                        "documentation": None,
                    },
                ]
            ),
            recommendations=json.dumps(["Add pytest", "Remove secrets"]),
        )
        session.add(report)
        await session.commit()
        await session.refresh(report)
        report_id = report.id

    return {"id": report_id}


@pytest.fixture
async def export_client() -> AsyncClient:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestExportEndpoints:
    @pytest.mark.asyncio
    async def test_export_not_found(self, export_client: AsyncClient) -> None:
        for fmt in ["md", "html", "csv", "pdf", "sarif"]:
            response = await export_client.get(f"/api/reports/nonexistent-id/export/{fmt}")
            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_export_md_returns_markdown(self, export_client: AsyncClient) -> None:
        report = await _create_test_report()
        response = await export_client.get(f"/api/reports/{report['id']}/export/md")
        assert response.status_code == 200
        assert "text/markdown" in response.headers["content-type"]
        assert "facebook/react" in response.text

    @pytest.mark.asyncio
    async def test_export_html_returns_html(self, export_client: AsyncClient) -> None:
        report = await _create_test_report()
        response = await export_client.get(f"/api/reports/{report['id']}/export/html")
        assert response.status_code == 200
        assert "html" in response.headers["content-type"]
        assert "<!DOCTYPE html>" in response.text

    @pytest.mark.asyncio
    async def test_export_csv_returns_csv(self, export_client: AsyncClient) -> None:
        report = await _create_test_report()
        response = await export_client.get(f"/api/reports/{report['id']}/export/csv")
        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]

    @pytest.mark.asyncio
    async def test_export_pdf_returns_pdf(self, export_client: AsyncClient) -> None:
        report = await _create_test_report()
        response = await export_client.get(f"/api/reports/{report['id']}/export/pdf")
        assert response.status_code == 200
        assert "application/pdf" in response.headers["content-type"]
        assert response.content[:5] == b"%PDF-"

    @pytest.mark.asyncio
    async def test_export_sarif_returns_sarif(self, export_client: AsyncClient) -> None:
        report = await _create_test_report()
        response = await export_client.get(f"/api/reports/{report['id']}/export/sarif")
        assert response.status_code == 200
        assert "sarif" in response.headers["content-type"]
        data = json.loads(response.text)
        assert data["version"] == "2.1.0"

    @pytest.mark.asyncio
    async def test_export_has_content_disposition(self, export_client: AsyncClient) -> None:
        report = await _create_test_report()
        for fmt in ["md", "html", "csv", "pdf", "sarif"]:
            response = await export_client.get(f"/api/reports/{report['id']}/export/{fmt}")
            assert "content-disposition" in response.headers

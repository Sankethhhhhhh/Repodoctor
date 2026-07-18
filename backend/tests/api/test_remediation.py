import json

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Report


class TestRemediationNotFound:
    @pytest.mark.asyncio
    async def test_remediation_report_not_found(self, client: AsyncClient, db_session: AsyncSession) -> None:
        response = await client.get("/api/reports/fake-report-id/remediate")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data


class TestRemediationAllPassed:
    @pytest.mark.asyncio
    async def test_remediation_all_passed(self, client: AsyncClient, db_session: AsyncSession) -> None:
        report = Report(
            repo_full_name="owner/perfectrepo",
            repo_url="https://github.com/owner/perfectrepo",
            commit_sha="shaPerf",
            score=100,
            grade="A+",
            category_breakdown=json.dumps(
                [
                    {"name": "Testing", "score": 10, "max_score": 10, "details": []},
                ]
            ),
            rules=json.dumps(
                [
                    {
                        "id": "R1",
                        "passed": True,
                        "rule": "has_readme",
                        "severity": "high",
                        "evidence": "Found README.md",
                    },
                    {
                        "id": "R2",
                        "passed": True,
                        "rule": "has_license",
                        "severity": "medium",
                        "evidence": "Found LICENSE",
                    },
                ]
            ),
            recommendations=json.dumps([]),
        )
        db_session.add(report)
        await db_session.flush()

        response = await client.get(f"/api/reports/{report.id}/remediate")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "no remediation" in data["message"].lower() or "all rules passed" in data["message"].lower()


class TestRemediationHasFailures:
    @pytest.mark.asyncio
    async def test_remediation_has_failures(self, client: AsyncClient, db_session: AsyncSession) -> None:
        report = Report(
            repo_full_name="owner/brokenrepo",
            repo_url="https://github.com/owner/brokenrepo",
            commit_sha="shaBroken",
            score=30,
            grade="F",
            category_breakdown=json.dumps(
                [
                    {"name": "Testing", "score": 2, "max_score": 10, "details": []},
                    {"name": "Security", "score": 1, "max_score": 10, "details": []},
                ]
            ),
            rules=json.dumps(
                [
                    {
                        "id": "R1",
                        "passed": True,
                        "rule": "has_readme",
                        "severity": "high",
                        "evidence": "Found README.md",
                    },
                    {
                        "id": "R2",
                        "passed": False,
                        "rule": "has_tests",
                        "severity": "high",
                        "evidence": "No test directory found",
                        "recommendation": "Add tests",
                    },
                    {
                        "id": "R3",
                        "passed": False,
                        "rule": "has_ci",
                        "severity": "medium",
                        "evidence": "No CI config",
                        "recommendation": "Add CI workflow",
                    },
                ]
            ),
            recommendations=json.dumps([]),
        )
        db_session.add(report)
        await db_session.flush()

        response = await client.get(f"/api/reports/{report.id}/remediate")
        assert response.status_code == 200
        data = response.json()
        assert "remediations" in data
        assert isinstance(data["remediations"], list)

import json
from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Report


class TestGetRepoHistory:
    @pytest.mark.asyncio
    async def test_get_repo_history_empty(self, client: AsyncClient, db_session: AsyncSession) -> None:
        response = await client.get("/api/reports/history/testowner/testrepo")
        assert response.status_code == 200
        data = response.json()
        assert data["reports"] == []
        assert data["total"] == 0
        assert data["repo_full_name"] == "testowner/testrepo"

    @pytest.mark.asyncio
    async def test_get_repo_history_returns_reports(self, client: AsyncClient, db_session: AsyncSession) -> None:
        now = datetime.now(UTC)
        report1 = Report(
            repo_full_name="testowner/testrepo",
            repo_url="https://github.com/testowner/testrepo",
            commit_sha="aaa111",
            score=70,
            grade="C",
            category_breakdown=json.dumps([{"name": "Testing", "score": 7, "max_score": 10, "details": []}]),
            rules=json.dumps([{"id": "R1", "passed": True}]),
            recommendations=json.dumps([]),
        )
        report2 = Report(
            repo_full_name="testowner/testrepo",
            repo_url="https://github.com/testowner/testrepo",
            commit_sha="bbb222",
            score=85,
            grade="B",
            category_breakdown=json.dumps([{"name": "Testing", "score": 8, "max_score": 10, "details": []}]),
            rules=json.dumps([{"id": "R1", "passed": True}]),
            recommendations=json.dumps([]),
        )
        db_session.add(report1)
        await db_session.flush()
        report1.created_at = now - timedelta(hours=1)
        db_session.add(report2)
        await db_session.flush()
        report2.created_at = now
        await db_session.flush()

        response = await client.get("/api/reports/history/testowner/testrepo")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["reports"]) == 2
        assert data["reports"][0]["commit_sha"] == "bbb222"
        assert data["reports"][1]["commit_sha"] == "aaa111"
        assert data["reports"][0]["score"] == 85
        assert data["reports"][1]["score"] == 70

    @pytest.mark.asyncio
    async def test_get_repo_history_not_found(self, client: AsyncClient, db_session: AsyncSession) -> None:
        response = await client.get("/api/reports/history/nobody/nosuchrepo")
        assert response.status_code == 200
        data = response.json()
        assert data["reports"] == []
        assert data["total"] == 0


class TestGetRepoTrends:
    @pytest.mark.asyncio
    async def test_get_repo_trends_empty(self, client: AsyncClient, db_session: AsyncSession) -> None:
        response = await client.get("/api/reports/trends/emptyowner/emptyrepo")
        assert response.status_code == 200
        data = response.json()
        assert data["data_points"] == []
        assert data["score_change"] is None
        assert data["grade_change"] is None

    @pytest.mark.asyncio
    async def test_get_repo_trends_returns_data(self, client: AsyncClient, db_session: AsyncSession) -> None:
        now = datetime.now(UTC)
        report1 = Report(
            repo_full_name="trendowner/trendrepo",
            repo_url="https://github.com/trendowner/trendrepo",
            commit_sha="sha111",
            score=60,
            grade="D",
            category_breakdown=json.dumps([{"name": "Security", "score": 6, "max_score": 10, "details": []}]),
            rules=json.dumps([{"id": "S1", "passed": False}]),
            recommendations=json.dumps([]),
        )
        report2 = Report(
            repo_full_name="trendowner/trendrepo",
            repo_url="https://github.com/trendowner/trendrepo",
            commit_sha="sha222",
            score=90,
            grade="A",
            category_breakdown=json.dumps([{"name": "Security", "score": 9, "max_score": 10, "details": []}]),
            rules=json.dumps([{"id": "S1", "passed": True}]),
            recommendations=json.dumps([]),
        )
        db_session.add(report1)
        await db_session.flush()
        report1.created_at = now - timedelta(hours=2)
        db_session.add(report2)
        await db_session.flush()
        report2.created_at = now
        await db_session.flush()

        response = await client.get("/api/reports/trends/trendowner/trendrepo")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data_points"]) == 2
        assert data["score_change"] == 30
        assert data["grade_change"] == "D -> A"

    @pytest.mark.asyncio
    async def test_get_repo_trends_single_report(self, client: AsyncClient, db_session: AsyncSession) -> None:
        report = Report(
            repo_full_name="singleowner/singlerepo",
            repo_url="https://github.com/singleowner/singlerepo",
            commit_sha="sha001",
            score=75,
            grade="B",
            category_breakdown=json.dumps([{"name": "Docs", "score": 7, "max_score": 10, "details": []}]),
            rules=json.dumps([]),
            recommendations=json.dumps([]),
        )
        db_session.add(report)
        await db_session.flush()

        response = await client.get("/api/reports/trends/singleowner/singlerepo")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data_points"]) == 1
        assert data["score_change"] is None
        assert data["grade_change"] is None

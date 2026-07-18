import json

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Report


class TestCompareReports:
    @pytest.mark.asyncio
    async def test_compare_reports(self, client: AsyncClient, db_session: AsyncSession) -> None:
        report_a = Report(
            repo_full_name="owner/repoA",
            repo_url="https://github.com/owner/repoA",
            commit_sha="shaA",
            score=80,
            grade="B",
            category_breakdown=json.dumps(
                [
                    {"name": "Testing", "score": 8, "max_score": 10, "details": []},
                    {"name": "Security", "score": 6, "max_score": 10, "details": []},
                ]
            ),
            rules=json.dumps([{"id": "R1", "passed": True}, {"id": "R2", "passed": False}]),
            recommendations=json.dumps([]),
        )
        report_b = Report(
            repo_full_name="owner/repoB",
            repo_url="https://github.com/owner/repoB",
            commit_sha="shaB",
            score=90,
            grade="A",
            category_breakdown=json.dumps(
                [
                    {"name": "Testing", "score": 9, "max_score": 10, "details": []},
                    {"name": "Security", "score": 8, "max_score": 10, "details": []},
                ]
            ),
            rules=json.dumps([{"id": "R1", "passed": True}, {"id": "R2", "passed": True}]),
            recommendations=json.dumps([]),
        )
        db_session.add(report_a)
        db_session.add(report_b)
        await db_session.flush()

        response = await client.post(
            "/api/compare",
            json={"report_id_a": report_a.id, "report_id_b": report_b.id},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["overall_winner"] == "B"
        assert data["score_difference"] == 10
        assert len(data["category_comparison"]) == 2
        assert "improvement_suggestions" in data

    @pytest.mark.asyncio
    async def test_compare_report_not_found(self, client: AsyncClient, db_session: AsyncSession) -> None:
        response = await client.post(
            "/api/compare",
            json={"report_id_a": "nonexistent-id-1", "report_id_b": "nonexistent-id-2"},
        )
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_compare_same_report(self, client: AsyncClient, db_session: AsyncSession) -> None:
        report = Report(
            repo_full_name="owner/samerepo",
            repo_url="https://github.com/owner/samerepo",
            commit_sha="shaSame",
            score=75,
            grade="C",
            category_breakdown=json.dumps(
                [
                    {"name": "Documentation", "score": 7, "max_score": 10, "details": []},
                ]
            ),
            rules=json.dumps([{"id": "R1", "passed": True}]),
            recommendations=json.dumps([]),
        )
        db_session.add(report)
        await db_session.flush()

        response = await client.post(
            "/api/compare",
            json={"report_id_a": report.id, "report_id_b": report.id},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["overall_winner"] == "Tie"
        assert data["score_difference"] == 0

    @pytest.mark.asyncio
    async def test_compare_category_comparison(self, client: AsyncClient, db_session: AsyncSession) -> None:
        report_a = Report(
            repo_full_name="owner/catA",
            repo_url="https://github.com/owner/catA",
            commit_sha="shaCatA",
            score=70,
            grade="C",
            category_breakdown=json.dumps(
                [
                    {"name": "Testing", "score": 5, "max_score": 10, "details": []},
                    {"name": "Security", "score": 8, "max_score": 10, "details": []},
                ]
            ),
            rules=json.dumps([]),
            recommendations=json.dumps([]),
        )
        report_b = Report(
            repo_full_name="owner/catB",
            repo_url="https://github.com/owner/catB",
            commit_sha="shaCatB",
            score=70,
            grade="C",
            category_breakdown=json.dumps(
                [
                    {"name": "Testing", "score": 9, "max_score": 10, "details": []},
                    {"name": "Security", "score": 4, "max_score": 10, "details": []},
                ]
            ),
            rules=json.dumps([]),
            recommendations=json.dumps([]),
        )
        db_session.add(report_a)
        db_session.add(report_b)
        await db_session.flush()

        response = await client.post(
            "/api/compare",
            json={"report_id_a": report_a.id, "report_id_b": report_b.id},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["overall_winner"] == "Tie"
        category_comparison = data["category_comparison"]
        testing_cat = next(c for c in category_comparison if c["name"] == "Testing")
        security_cat = next(c for c in category_comparison if c["name"] == "Security")
        assert testing_cat["winner"] == "B"
        assert security_cat["winner"] == "A"

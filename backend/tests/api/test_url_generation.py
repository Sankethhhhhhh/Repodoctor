import json

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client() -> AsyncClient:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def _insert_report(**kwargs: object) -> str:
    from app.core.database import async_session_factory
    from app.models.models import Report

    defaults: dict[str, object] = {
        "repo_full_name": "test/repo",
        "repo_url": "https://github.com/test/repo",
        "commit_sha": "abc123",
        "score": 80,
        "grade": "B",
        "category_breakdown": json.dumps([]),
        "rules": json.dumps([]),
        "recommendations": json.dumps([]),
    }
    defaults.update(kwargs)
    async with async_session_factory() as session:
        report = Report(**defaults)  # type: ignore[arg-type]
        session.add(report)
        await session.commit()
        await session.refresh(report)
        return str(report.id)


class TestGitHubURLGeneration:
    def test_build_repo_url_basic(self) -> None:
        from app.api.report_service import build_repo_url

        url = build_repo_url("facebook", "react")
        assert url == "https://github.com/facebook/react"

    def test_build_repo_url_with_dashes(self) -> None:
        from app.api.report_service import build_repo_url

        url = build_repo_url("my-org", "my-repo-name")
        assert url == "https://github.com/my-org/my-repo-name"

    def test_build_repo_url_with_dots(self) -> None:
        from app.api.report_service import build_repo_url

        url = build_repo_url("user.name", "repo.name")
        assert url == "https://github.com/user.name/repo.name"

    def test_always_returns_https(self) -> None:
        from app.api.report_service import build_repo_url

        for owner, repo in [("a", "b"), ("org", "project"), ("test", "repo")]:
            url = build_repo_url(owner, repo)
            assert url.startswith("https://github.com/")

    @pytest.mark.asyncio
    async def test_get_report_returns_full_url(self, client: AsyncClient) -> None:
        report_id = await _insert_report()
        response = await client.get(f"/api/reports/{report_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["repo_url"] == "https://github.com/test/repo"

    @pytest.mark.asyncio
    async def test_list_reports_returns_full_url(self, client: AsyncClient) -> None:
        await _insert_report()
        response = await client.get("/api/reports")
        assert response.status_code == 200
        data = response.json()
        urls = [r["repo_url"] for r in data["reports"]]
        assert "https://github.com/test/repo" in urls

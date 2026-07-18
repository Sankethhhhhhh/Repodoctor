"""Regression tests for error handling and GitHub token integration."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient
from app.github.client import (
    GitHubClient,
    GitHubError,
    GitHubNotFoundError,
    GitHubRateLimitError,
)
from app.github.service import GitHubService
from app.main import app
from app.api.reports_router import _get_report_service, ReportService


class TestGitHubClientTokenResolution:
    """Verify the client correctly resolves tokens from settings."""

    def test_explicit_token_takes_precedence(self) -> None:
        with patch("app.github.client.settings") as mock_settings:
            mock_settings.github_token = "pat_from_settings"
            mock_settings.github_client_secret = "secret_from_settings"
            client = GitHubClient(token="explicit_token")
            auth = client._client.headers.get("authorization", "")
            assert auth == "Bearer explicit_token"
            assert client._authenticated is True

    def test_falls_back_to_settings_github_token(self) -> None:
        with patch("app.github.client.settings") as mock_settings:
            mock_settings.github_token = "pat_from_settings"
            mock_settings.github_client_secret = ""
            client = GitHubClient()
            auth = client._client.headers.get("authorization", "")
            assert auth == "Bearer pat_from_settings"
            assert client._authenticated is True

    def test_falls_back_to_client_secret(self) -> None:
        with patch("app.github.client.settings") as mock_settings:
            mock_settings.github_token = ""
            mock_settings.github_client_secret = "oauth_secret"
            client = GitHubClient()
            auth = client._client.headers.get("authorization", "")
            assert auth == "Bearer oauth_secret"
            assert client._authenticated is True

    def test_no_auth_when_no_tokens(self) -> None:
        with patch("app.github.client.settings") as mock_settings:
            mock_settings.github_token = ""
            mock_settings.github_client_secret = ""
            client = GitHubClient()
            auth = client._client.headers.get("authorization", "")
            assert auth == ""
            assert client._authenticated is False


def _make_failing_service(exc: Exception) -> MagicMock:
    mock_service = MagicMock(spec=ReportService)
    mock_service.analyze = AsyncMock(side_effect=exc)
    return mock_service


def _override_with_mock(service: MagicMock):
    async def _override():
        return service
    return _override


class TestReportsAPIErrorHandling:
    """Test the POST /api/reports endpoint returns proper HTTP status codes."""

    @pytest.mark.asyncio
    async def test_invalid_url_returns_400(self, client: AsyncClient) -> None:
        response = await client.post("/api/reports", json={"url": "not-a-url"})
        assert response.status_code == 400
        assert "Invalid" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_empty_url_returns_400(self, client: AsyncClient) -> None:
        response = await client.post("/api/reports", json={"url": ""})
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_missing_url_field_returns_422(self, client: AsyncClient) -> None:
        response = await client.post("/api/reports", json={})
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_nonexistent_repo_returns_404(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/reports",
            json={"url": "https://github.com/this-does-not-exist-xyz/repo"},
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_github_rate_limit_returns_502(self, client: AsyncClient) -> None:
        mock = _make_failing_service(GitHubRateLimitError("Rate limit exceeded"))
        app.dependency_overrides[_get_report_service] = _override_with_mock(mock)
        try:
            response = await client.post(
                "/api/reports",
                json={"url": "https://github.com/facebook/react"},
            )
            assert response.status_code == 502
            assert "rate limit" in response.json()["detail"].lower()
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_github_not_found_returns_404(self, client: AsyncClient) -> None:
        mock = _make_failing_service(GitHubNotFoundError("Repository not found"))
        app.dependency_overrides[_get_report_service] = _override_with_mock(mock)
        try:
            response = await client.post(
                "/api/reports",
                json={"url": "https://github.com/owner/repo"},
            )
            assert response.status_code == 404
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_github_api_error_returns_502(self, client: AsyncClient) -> None:
        mock = _make_failing_service(GitHubError("API error", status_code=500))
        app.dependency_overrides[_get_report_service] = _override_with_mock(mock)
        try:
            response = await client.post(
                "/api/reports",
                json={"url": "https://github.com/facebook/react"},
            )
            assert response.status_code == 502
            assert "GitHub API error" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_unexpected_error_returns_500_with_detail(self, client: AsyncClient) -> None:
        mock = _make_failing_service(RuntimeError("Something broke unexpectedly"))
        app.dependency_overrides[_get_report_service] = _override_with_mock(mock)
        try:
            response = await client.post(
                "/api/reports",
                json={"url": "https://github.com/facebook/react"},
            )
            assert response.status_code == 500
            detail = response.json()["detail"]
            assert "RuntimeError" in detail
            assert "Something broke unexpectedly" in detail
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_network_timeout_returns_502(self, client: AsyncClient) -> None:
        mock = _make_failing_service(GitHubError("GitHub API request timed out"))
        app.dependency_overrides[_get_report_service] = _override_with_mock(mock)
        try:
            response = await client.post(
                "/api/reports",
                json={"url": "https://github.com/facebook/react"},
            )
            assert response.status_code == 502
        finally:
            app.dependency_overrides.clear()


class TestGitHubClientErrorHandling:
    """Test GitHub client error classification."""

    @pytest.mark.asyncio
    async def test_rate_limit_error_on_zero_remaining(self) -> None:
        client = GitHubClient.__new__(GitHubClient)
        client._client = AsyncMock()
        client._authenticated = True

        response = MagicMock()
        response.status_code = 403
        response.headers = {
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Reset": "1700000000",
        }
        client._client.get = AsyncMock(return_value=response)

        with pytest.raises(GitHubRateLimitError):
            await client._get("/repos/test/repo")

    @pytest.mark.asyncio
    async def test_forbidden_not_rate_limit(self) -> None:
        client = GitHubClient.__new__(GitHubClient)
        client._client = AsyncMock()
        client._authenticated = True

        response = MagicMock()
        response.status_code = 403
        response.headers = {"X-RateLimit-Remaining": "10"}
        client._client.get = AsyncMock(return_value=response)

        with pytest.raises(GitHubError) as exc_info:
            await client._get("/repos/private/repo")
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_401_raises_auth_error(self) -> None:
        client = GitHubClient.__new__(GitHubClient)
        client._client = AsyncMock()
        client._authenticated = True

        response = MagicMock()
        response.status_code = 401
        response.headers = {}
        client._client.get = AsyncMock(return_value=response)

        with pytest.raises(GitHubError) as exc_info:
            await client._get("/repos/test/repo")
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_404_raises_not_found(self) -> None:
        client = GitHubClient.__new__(GitHubClient)
        client._client = AsyncMock()
        client._authenticated = True

        response = MagicMock()
        response.status_code = 404
        response.headers = {}
        client._client.get = AsyncMock(return_value=response)

        with pytest.raises(GitHubNotFoundError):
            await client._get("/repos/nonexistent/repo")

    @pytest.mark.asyncio
    async def test_server_error_raises_generic_error(self) -> None:
        client = GitHubClient.__new__(GitHubClient)
        client._client = AsyncMock()
        client._authenticated = True

        response = MagicMock()
        response.status_code = 500
        response.headers = {}
        response.text = "Internal Server Error"
        client._client.get = AsyncMock(return_value=response)

        with pytest.raises(GitHubError) as exc_info:
            await client._get("/repos/test/repo")
        assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_readme_not_found_returns_none(self) -> None:
        client = GitHubClient.__new__(GitHubClient)
        client._client = AsyncMock()
        client._authenticated = True

        response = MagicMock()
        response.status_code = 404
        response.headers = {}
        client._client.get = AsyncMock(return_value=response)

        result = await client.get_readme("test", "repo")
        assert result is None

    @pytest.mark.asyncio
    async def test_tree_error_returns_empty_list(self) -> None:
        client = GitHubClient.__new__(GitHubClient)
        client._client = AsyncMock()
        client._authenticated = True

        response = MagicMock()
        response.status_code = 500
        response.headers = {}
        response.text = "error"
        client._client.get = AsyncMock(return_value=response)

        result = await client.get_tree("test", "repo", "main")
        assert result == []

    @pytest.mark.asyncio
    async def test_workflows_error_returns_empty_list(self) -> None:
        client = GitHubClient.__new__(GitHubClient)
        client._client = AsyncMock()
        client._authenticated = True

        response = MagicMock()
        response.status_code = 500
        response.headers = {}
        response.text = "error"
        client._client.get = AsyncMock(return_value=response)

        result = await client.get_workflows("test", "repo")
        assert result == []

    @pytest.mark.asyncio
    async def test_releases_error_returns_empty_list(self) -> None:
        client = GitHubClient.__new__(GitHubClient)
        client._client = AsyncMock()
        client._authenticated = True

        response = MagicMock()
        response.status_code = 500
        response.headers = {}
        response.text = "error"
        client._client.get = AsyncMock(return_value=response)

        result = await client.get_releases("test", "repo")
        assert result == []

    @pytest.mark.asyncio
    async def test_license_not_found_returns_none(self) -> None:
        client = GitHubClient.__new__(GitHubClient)
        client._client = AsyncMock()
        client._authenticated = True

        response = MagicMock()
        response.status_code = 404
        response.headers = {}
        client._client.get = AsyncMock(return_value=response)

        result = await client.get_license("test", "repo")
        assert result is None


class TestServiceResilience:
    """Test that the service layer handles partial failures gracefully."""

    @pytest.mark.asyncio
    async def test_missing_files_in_repo(self) -> None:
        """A repo with an empty tree should still score (low score but no crash)."""
        from app.github.schemas import GitHubRepositoryData, RepositoryInfo
        from app.scoring.pipeline import run_scoring

        data = GitHubRepositoryData(
            repo=RepositoryInfo(
                full_name="test/empty",
                name="empty",
                owner="test",
                description=None,
                default_branch="main",
                created_at="2026-01-01T00:00:00Z",
                updated_at="2026-01-01T00:00:00Z",
                pushed_at="2026-01-01T00:00:00Z",
                stargazers_count=0,
                forks_count=0,
                open_issues_count=0,
                language=None,
                topics=[],
            ),
            readme=None,
            tree=[],
            commits=[],
            workflows=[],
            license=None,
            has_gitignore=False,
            has_dockerfile=False,
            releases=[],
        )
        result = run_scoring(data)
        assert result.overall_score >= 0
        assert result.overall_score <= 100
        assert len(result.rules) == 31

    @pytest.mark.asyncio
    async def test_invalid_url_parse(self) -> None:
        from app.github.service import parse_repo_url

        with pytest.raises(ValueError, match="Invalid repository URL"):
            parse_repo_url("")

        with pytest.raises(ValueError):
            parse_repo_url("https://not-github.com/repo")

        with pytest.raises(ValueError):
            parse_repo_url("just some random text")

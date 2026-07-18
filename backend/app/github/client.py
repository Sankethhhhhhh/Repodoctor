import logging
import time
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

GITHUB_API_BASE = "https://api.github.com"


class GitHubError(Exception):
    def __init__(self, message: str, status_code: int | None = None) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class GitHubRateLimitError(GitHubError):
    def __init__(self, message: str, reset_at: str | None = None) -> None:
        self.reset_at = reset_at
        super().__init__(message, status_code=403)


class GitHubNotFoundError(GitHubError):
    def __init__(self, message: str = "Repository not found") -> None:
        super().__init__(message, status_code=404)


class GitHubClient:
    def __init__(self, token: str | None = None) -> None:
        headers = {"Accept": "application/vnd.github.v3+json"}
        resolved_token = token or settings.github_token or settings.github_client_secret or None
        if resolved_token:
            headers["Authorization"] = f"Bearer {resolved_token}"

        self._client = httpx.AsyncClient(
            base_url=GITHUB_API_BASE,
            headers=headers,
            timeout=30.0,
            follow_redirects=True,
        )
        self._authenticated = resolved_token is not None

    async def close(self) -> None:
        await self._client.aclose()

    async def _get(self, path: str) -> Any:  # noqa: ANN401
        start = time.monotonic()
        try:
            response = await self._client.get(path)
        except httpx.TimeoutException as e:
            elapsed = time.monotonic() - start
            logger.error("GitHub API timeout after %.1fs: %s", elapsed, path)
            raise GitHubError("GitHub API request timed out") from e
        except httpx.RequestError as e:
            elapsed = time.monotonic() - start
            logger.error("GitHub API connection error after %.1fs: %s", elapsed, path)
            raise GitHubError("Failed to connect to GitHub API") from e

        elapsed = time.monotonic() - start
        remaining = response.headers.get("X-RateLimit-Remaining", "?")
        logger.debug("GitHub API %s -> %d (%.1fs, remaining=%s)", path, response.status_code, elapsed, remaining)

        if response.status_code == 404:
            raise GitHubNotFoundError(f"Resource not found: {path}")

        if response.status_code == 403:
            reset_at = response.headers.get("X-RateLimit-Reset")
            remaining = response.headers.get("X-RateLimit-Remaining", "0")
            if remaining == "0":
                logger.error("GitHub rate limit exceeded on %s (reset=%s)", path, reset_at)
                raise GitHubRateLimitError(
                    "GitHub API rate limit exceeded",
                    reset_at=reset_at,
                )
            raise GitHubError(
                "GitHub API access forbidden",
                status_code=403,
            )

        if response.status_code == 401:
            raise GitHubError("GitHub API authentication failed", status_code=401)

        if response.status_code >= 400:
            logger.error(
                "GitHub API error %d: %s",
                response.status_code,
                response.text[:200],
            )
            raise GitHubError(
                f"GitHub API error: {response.status_code}",
                status_code=response.status_code,
            )

        return response.json()

    async def _get_text(self, path: str) -> str:
        try:
            response = await self._client.get(path)
        except httpx.TimeoutException as e:
            raise GitHubError("GitHub API request timed out") from e
        except httpx.RequestError as e:
            raise GitHubError("Failed to connect to GitHub API") from e

        if response.status_code == 404:
            return ""

        if response.status_code >= 400:
            raise GitHubError(
                f"GitHub API error: {response.status_code}",
                status_code=response.status_code,
            )

        return response.text

    async def get_repository(self, owner: str, repo: str) -> dict[str, Any]:
        result: dict[str, Any] = await self._get(f"/repos/{owner}/{repo}")
        return result

    async def get_readme(self, owner: str, repo: str) -> str | None:
        try:
            data = await self._get(f"/repos/{owner}/{repo}/readme")
            import base64

            content = data.get("content", "")
            encoding = data.get("encoding", "")
            if encoding == "base64" and content:
                try:
                    return base64.b64decode(content).decode("utf-8", errors="replace")
                except Exception:
                    logger.warning("Failed to decode README base64 content")
                    return None
            download_url = data.get("download_url")
            if download_url:
                return await self._get_text(download_url.replace(GITHUB_API_BASE, ""))
            return None
        except GitHubNotFoundError:
            return None

    async def get_tree(self, owner: str, repo: str, sha: str = "HEAD") -> list[dict[str, Any]]:
        try:
            data: dict[str, Any] = await self._get(f"/repos/{owner}/{repo}/git/trees/{sha}?recursive=1")
            tree: list[dict[str, Any]] = data.get("tree", [])
            return tree
        except GitHubError:
            return []

    async def get_commits(self, owner: str, repo: str, limit: int = 100) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = await self._get(f"/repos/{owner}/{repo}/commits?per_page={limit}")
        return result

    async def get_workflows(self, owner: str, repo: str) -> list[dict[str, Any]]:
        try:
            data: dict[str, Any] = await self._get(f"/repos/{owner}/{repo}/actions/workflows")
            workflows: list[dict[str, Any]] = data.get("workflows", [])
            return workflows
        except GitHubError:
            return []

    async def get_license(self, owner: str, repo: str) -> dict[str, Any] | None:
        try:
            result: dict[str, Any] = await self._get(f"/repos/{owner}/{repo}/license")
            return result
        except GitHubNotFoundError:
            return None
        except GitHubError:
            return None

    async def get_releases(self, owner: str, repo: str) -> list[dict[str, Any]]:
        try:
            result: list[dict[str, Any]] = await self._get(f"/repos/{owner}/{repo}/releases?per_page=10")
            return result
        except GitHubNotFoundError:
            return []
        except GitHubError:
            return []

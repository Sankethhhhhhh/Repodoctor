import base64
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.github.client import GitHubClient, GitHubNotFoundError
from app.github.service import GitHubService

MOCK_REPO_RESPONSE = {
    "full_name": "facebook/react",
    "name": "react",
    "owner": {"login": "facebook"},
    "description": "The library for web and native user interfaces",
    "default_branch": "main",
    "created_at": "2013-05-24T16:15:54Z",
    "updated_at": "2026-07-15T10:00:00Z",
    "pushed_at": "2026-07-15T12:00:00Z",
    "stargazers_count": 230000,
    "forks_count": 47000,
    "open_issues_count": 1000,
    "language": "JavaScript",
    "topics": ["javascript", "react", "ui"],
}


def _tree_item(
    path: str,
    type_: str = "blob",
    sha: str = "abc",
    size: int = 100,
) -> dict[str, object]:
    return {
        "path": path,
        "mode": "100644",
        "type": type_,
        "sha": sha,
        "size": size,
        "url": "",
    }


MOCK_TREE_RESPONSE = {
    "tree": [
        _tree_item("README.md", size=5000, sha="a1"),
        _tree_item("package.json", size=2000, sha="a2"),
        _tree_item("src", type_="tree", sha="a3"),
        _tree_item(".gitignore", size=300, sha="a4"),
        _tree_item("Dockerfile", size=500, sha="a5"),
    ]
}


def _commit_data(
    sha: str,
    message: str,
    author_name: str,
    date: str,
) -> dict[str, object]:
    return {
        "sha": sha,
        "commit": {
            "message": message,
            "author": {
                "name": author_name,
                "email": f"{author_name.lower()}@test.com",
                "date": date,
            },
            "committer": {
                "name": author_name,
                "date": date,
            },
        },
    }


MOCK_COMMITS_RESPONSE = [
    _commit_data(
        "abc123",
        "Update README with new usage examples",
        "Dan Abramov",
        "2026-07-15T12:00:00Z",
    ),
    _commit_data(
        "def456",
        "Fix memory leak in concurrent mode",
        "Andrew Clark",
        "2026-07-14T10:00:00Z",
    ),
]

MOCK_WORKFLOWS_RESPONSE = {
    "workflows": [
        {
            "path": ".github/workflows/test.yml",
            "name": "Tests",
            "state": "active",
        },
        {
            "path": ".github/workflows/lint.yml",
            "name": "Lint",
            "state": "active",
        },
    ]
}

MOCK_LICENSE_RESPONSE = {
    "license": {
        "spdx_id": "MIT",
        "name": "MIT License",
    }
}

_README_CONTENT = b"# React\n\nThe library for web and native user interfaces."

MOCK_README_RESPONSE = {
    "content": base64.b64encode(_README_CONTENT).decode(),
    "encoding": "base64",
    "download_url": ("https://raw.githubusercontent.com/facebook/react/main/README.md"),
}


@pytest.fixture
def mock_client() -> GitHubClient:
    client = GitHubClient.__new__(GitHubClient)
    client._client = AsyncMock()
    return client


@pytest.fixture
def service(mock_client: GitHubClient) -> GitHubService:
    return GitHubService(client=mock_client)


class TestGitHubClientGetRepository:
    @pytest.mark.asyncio
    async def test_success(self, mock_client: GitHubClient) -> None:
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = MOCK_REPO_RESPONSE
        mock_client._client.get = AsyncMock(return_value=response)

        result = await mock_client.get_repository("facebook", "react")
        assert result["full_name"] == "facebook/react"
        mock_client._client.get.assert_called_once_with("/repos/facebook/react")

    @pytest.mark.asyncio
    async def test_not_found(self, mock_client: GitHubClient) -> None:
        response = MagicMock()
        response.status_code = 404
        response.headers = {}
        mock_client._client.get = AsyncMock(return_value=response)

        with pytest.raises(GitHubNotFoundError):
            await mock_client.get_repository("facebook", "nonexistent")


class TestGitHubServiceFetchRepositoryData:
    @pytest.mark.asyncio
    async def test_full_fetch(self, service: GitHubService) -> None:
        def make_response(data: dict | list, status: int = 200) -> MagicMock:
            resp = MagicMock()
            resp.status_code = status
            resp.json.return_value = data
            resp.headers = {"X-RateLimit-Remaining": "50"}
            resp.text = ""
            return resp

        responses = [
            make_response(MOCK_REPO_RESPONSE),
            make_response(MOCK_README_RESPONSE),
            make_response(MOCK_TREE_RESPONSE),
            make_response(MOCK_COMMITS_RESPONSE),
            make_response(MOCK_WORKFLOWS_RESPONSE),
            make_response(MOCK_LICENSE_RESPONSE),
            make_response([{"tag_name": "v18.3.1", "name": "18.3.1"}]),
        ]

        call_count = 0

        async def mock_get(
            _path: str,
        ) -> MagicMock:
            nonlocal call_count
            resp = responses[call_count]
            call_count += 1
            return resp

        service._client._client.get = mock_get

        data = await service.fetch_repository_data("facebook", "react")

        assert data.repo.full_name == "facebook/react"
        assert data.repo.owner == "facebook"
        assert data.repo.stargazers_count == 230000
        assert len(data.tree) == 5
        assert len(data.commits) == 2
        assert len(data.workflows) == 2
        assert data.license is not None
        assert data.license.spdx_id == "MIT"
        assert data.has_gitignore is True
        assert data.has_dockerfile is True
        assert len(data.releases) == 1
        assert data.releases[0].tag_name == "v18.3.1"

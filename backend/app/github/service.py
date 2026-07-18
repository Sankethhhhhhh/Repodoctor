import logging
import re

from app.github.client import GitHubClient
from app.github.schemas import (
    CommitInfo,
    GitHubRepositoryData,
    LicenseInfo,
    ReleaseInfo,
    RepositoryInfo,
    TreeNode,
    WorkflowFile,
)

logger = logging.getLogger(__name__)

REPO_URL_PATTERN = re.compile(r"(?:https?://github\.com/)?([a-zA-Z0-9._-]+)/([a-zA-Z0-9._-]+?)(?:\.git)?$")


def parse_repo_url(url: str) -> tuple[str, str]:
    match = REPO_URL_PATTERN.match(url.strip().rstrip("/"))
    if not match:
        raise ValueError(f"Invalid repository URL: {url}")
    return match.group(1), match.group(2)


class GitHubService:
    def __init__(self, client: GitHubClient | None = None) -> None:
        self._client = client or GitHubClient()

    async def close(self) -> None:
        await self._client.close()

    async def fetch_repository_data(self, owner: str, repo: str) -> GitHubRepositoryData:
        repo_data = await self._client.get_repository(owner, repo)

        readme = await self._client.get_readme(owner, repo)

        default_branch = repo_data.get("default_branch", "main")
        tree_data = await self._client.get_tree(owner, repo, default_branch)
        tree = [
            TreeNode(
                path=item["path"],
                mode=item.get("mode", ""),
                type=item.get("type", ""),
                sha=item.get("sha", ""),
                size=item.get("size"),
                url=item.get("url", ""),
            )
            for item in tree_data
            if isinstance(item, dict) and item.get("type") in ("blob", "tree")
        ]

        commits_data = await self._client.get_commits(owner, repo)
        commits = [
            CommitInfo(
                sha=c["sha"],
                message=c["commit"]["message"],
                author_name=c["commit"].get("author", {}).get("name"),
                author_email=c["commit"].get("author", {}).get("email"),
                author_date=c["commit"].get("author", {}).get("date", ""),
                committer_name=c["commit"].get("committer", {}).get("name"),
                committer_date=c["commit"].get("committer", {}).get("date", ""),
            )
            for c in commits_data
            if isinstance(c, dict) and "sha" in c and "commit" in c
        ]

        workflows_data = await self._client.get_workflows(owner, repo)
        workflows = [
            WorkflowFile(
                path=w.get("path", ""),
                name=w.get("name"),
                state=w.get("state"),
            )
            for w in workflows_data
            if isinstance(w, dict)
        ]

        license_data = await self._client.get_license(owner, repo)
        license_info = None
        if license_data and "license" in license_data:
            spdx = license_data["license"].get("spdx_id")
            name = license_data["license"].get("name")
            license_info = LicenseInfo(spdx_id=spdx, name=name)

        releases_data = await self._client.get_releases(owner, repo)
        releases = [
            ReleaseInfo(
                tag_name=r.get("tag_name", ""),
                name=r.get("name"),
            )
            for r in releases_data
            if isinstance(r, dict)
        ]

        file_paths = {item.path for item in tree}
        has_gitignore = ".gitignore" in file_paths
        has_dockerfile = "Dockerfile" in file_paths or any(p.startswith("docker/") for p in file_paths)

        repo_info = RepositoryInfo(
            full_name=repo_data["full_name"],
            name=repo_data["name"],
            owner=repo_data["owner"]["login"],
            description=repo_data.get("description"),
            default_branch=repo_data.get("default_branch", "main"),
            created_at=repo_data.get("created_at", ""),
            updated_at=repo_data.get("updated_at", ""),
            pushed_at=repo_data.get("pushed_at", ""),
            stargazers_count=repo_data.get("stargazers_count", 0),
            forks_count=repo_data.get("forks_count", 0),
            open_issues_count=repo_data.get("open_issues_count", 0),
            language=repo_data.get("language"),
            topics=repo_data.get("topics", []),
        )

        return GitHubRepositoryData(
            repo=repo_info,
            readme=readme,
            tree=tree,
            commits=commits,
            workflows=workflows,
            license=license_info,
            has_gitignore=has_gitignore,
            has_dockerfile=has_dockerfile,
            releases=releases,
        )

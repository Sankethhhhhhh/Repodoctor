from __future__ import annotations

from pydantic import BaseModel


class RepositoryInfo(BaseModel):
    full_name: str
    name: str
    owner: str
    description: str | None
    default_branch: str
    created_at: str
    updated_at: str
    pushed_at: str
    stargazers_count: int
    forks_count: int
    open_issues_count: int
    language: str | None
    topics: list[str]


class TreeNode(BaseModel):
    path: str
    mode: str
    type: str
    sha: str
    size: int | None
    url: str


class CommitInfo(BaseModel):
    sha: str
    message: str
    author_name: str | None
    author_email: str | None
    author_date: str
    committer_name: str | None
    committer_date: str


class WorkflowFile(BaseModel):
    path: str
    name: str | None
    state: str | None


class LicenseInfo(BaseModel):
    spdx_id: str | None
    name: str | None


class ReleaseInfo(BaseModel):
    tag_name: str
    name: str | None = None


class GitHubRepositoryData(BaseModel):
    repo: RepositoryInfo
    readme: str | None
    tree: list[TreeNode]
    commits: list[CommitInfo]
    workflows: list[WorkflowFile]
    license: LicenseInfo | None
    has_gitignore: bool
    has_dockerfile: bool
    releases: list[ReleaseInfo] = []

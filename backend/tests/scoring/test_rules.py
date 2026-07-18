from app.github.schemas import (
    CommitInfo,
    GitHubRepositoryData,
    LicenseInfo,
    RepositoryInfo,
    TreeNode,
    WorkflowFile,
)
from app.scoring.cicd import CI_CD_RULES
from app.scoring.documentation import DOCUMENTATION_RULES
from app.scoring.git_hygiene import GIT_HYGIENE_RULES
from app.scoring.licensing import LICENSING_RULES
from app.scoring.security import SECURITY_RULES
from app.scoring.testing import TESTING_RULES


def _make_data(**kwargs: object) -> GitHubRepositoryData:
    defaults: dict[str, object] = {
        "repo": RepositoryInfo(
            full_name="test/repo",
            name="repo",
            owner="test",
            description="Test",
            default_branch="main",
            created_at="2026-01-01T00:00:00Z",
            updated_at="2026-07-01T00:00:00Z",
            pushed_at="2026-07-01T00:00:00Z",
            stargazers_count=0,
            forks_count=0,
            open_issues_count=0,
            language=None,
            topics=[],
        ),
        "readme": None,
        "tree": [],
        "commits": [],
        "workflows": [],
        "license": None,
        "has_gitignore": False,
        "has_dockerfile": False,
    }
    defaults.update(kwargs)
    return GitHubRepositoryData(**defaults)  # type: ignore[arg-type]


class TestDocumentationRules:
    def test_readme_exists_pass(self) -> None:
        data = _make_data(readme="# Hello")
        result = DOCUMENTATION_RULES[0].evaluate(data)
        assert result.passed is True

    def test_readme_exists_fail(self) -> None:
        data = _make_data(readme=None)
        result = DOCUMENTATION_RULES[0].evaluate(data)
        assert result.passed is False

    def test_readme_length_pass(self) -> None:
        data = _make_data(readme="x" * 300)
        result = DOCUMENTATION_RULES[1].evaluate(data)
        assert result.passed is True

    def test_readme_length_fail(self) -> None:
        data = _make_data(readme="hi")
        result = DOCUMENTATION_RULES[1].evaluate(data)
        assert result.passed is False

    def test_readme_sections_pass(self) -> None:
        data = _make_data(
            readme="# Project\n\n## Installation\n\nnpm install\n\n## Usage\n\nRun it\n\n## License\n\nMIT"
        )
        result = DOCUMENTATION_RULES[2].evaluate(data)
        assert result.passed is True

    def test_readme_sections_fail(self) -> None:
        data = _make_data(readme="# Project\n\nJust a readme")
        result = DOCUMENTATION_RULES[2].evaluate(data)
        assert result.passed is False

    def test_contributing_exists_pass(self) -> None:
        data = _make_data(
            tree=[
                TreeNode(
                    path="CONTRIBUTING.md",
                    mode="100644",
                    type="blob",
                    sha="a",
                    size=100,
                    url="",
                ),
            ]
        )
        result = DOCUMENTATION_RULES[3].evaluate(data)
        assert result.passed is True

    def test_contributing_exists_fail(self) -> None:
        data = _make_data(tree=[])
        result = DOCUMENTATION_RULES[3].evaluate(data)
        assert result.passed is False


class TestTestingRules:
    def test_test_directory_pass(self) -> None:
        data = _make_data(
            tree=[
                TreeNode(
                    path="tests/test_main.py",
                    mode="100644",
                    type="blob",
                    sha="a",
                    size=100,
                    url="",
                ),
            ]
        )
        result = TESTING_RULES[0].evaluate(data)
        assert result.passed is True

    def test_test_directory_fail(self) -> None:
        data = _make_data(tree=[])
        result = TESTING_RULES[0].evaluate(data)
        assert result.passed is False

    def test_test_framework_pass(self) -> None:
        data = _make_data(
            tree=[
                TreeNode(
                    path="conftest.py",
                    mode="100644",
                    type="blob",
                    sha="a",
                    size=100,
                    url="",
                ),
            ]
        )
        result = TESTING_RULES[1].evaluate(data)
        assert result.passed is True

    def test_test_framework_fail(self) -> None:
        data = _make_data(tree=[])
        result = TESTING_RULES[1].evaluate(data)
        assert result.passed is False

    def test_coverage_config_pass(self) -> None:
        data = _make_data(
            tree=[
                TreeNode(
                    path=".coveragerc",
                    mode="100644",
                    type="blob",
                    sha="a",
                    size=50,
                    url="",
                ),
            ]
        )
        result = TESTING_RULES[2].evaluate(data)
        assert result.passed is True

    def test_ci_test_workflow_pass(self) -> None:
        data = _make_data(
            workflows=[
                WorkflowFile(path=".github/workflows/test.yml", name="Tests", state="active"),
            ]
        )
        result = TESTING_RULES[3].evaluate(data)
        assert result.passed is True

    def test_ci_test_workflow_fail(self) -> None:
        data = _make_data(workflows=[])
        result = TESTING_RULES[3].evaluate(data)
        assert result.passed is False


class TestCICDRules:
    def test_github_actions_pass(self) -> None:
        data = _make_data(
            workflows=[
                WorkflowFile(path=".github/workflows/ci.yml", name="CI", state="active"),
            ]
        )
        result = CI_CD_RULES[0].evaluate(data)
        assert result.passed is True

    def test_github_actions_fail(self) -> None:
        data = _make_data(workflows=[])
        result = CI_CD_RULES[0].evaluate(data)
        assert result.passed is False

    def test_build_workflow_pass(self) -> None:
        data = _make_data(
            workflows=[
                WorkflowFile(path=".github/workflows/build.yml", name="Build", state="active"),
            ]
        )
        result = CI_CD_RULES[1].evaluate(data)
        assert result.passed is True

    def test_lint_workflow_pass(self) -> None:
        data = _make_data(
            workflows=[
                WorkflowFile(path=".github/workflows/lint.yml", name="Lint", state="active"),
            ]
        )
        result = CI_CD_RULES[2].evaluate(data)
        assert result.passed is True

    def test_deploy_workflow_pass(self) -> None:
        data = _make_data(
            workflows=[
                WorkflowFile(path=".github/workflows/deploy.yml", name="Deploy", state="active"),
            ]
        )
        result = CI_CD_RULES[3].evaluate(data)
        assert result.passed is True


class TestGitHygieneRules:
    def test_meaningful_commits_pass(self) -> None:
        data = _make_data(
            commits=[
                CommitInfo(
                    sha="a",
                    message="Add user authentication with OAuth",
                    author_name="A",
                    author_email="a@t.com",
                    author_date="2026-01-01T00:00:00Z",
                    committer_name="A",
                    committer_date="2026-01-01T00:00:00Z",
                ),
                CommitInfo(
                    sha="b",
                    message="Fix memory leak in cache layer",
                    author_name="A",
                    author_email="a@t.com",
                    author_date="2026-01-02T00:00:00Z",
                    committer_name="A",
                    committer_date="2026-01-02T00:00:00Z",
                ),
            ]
        )
        result = GIT_HYGIENE_RULES[0].evaluate(data)
        assert result.passed is True

    def test_meaningful_commits_fail(self) -> None:
        data = _make_data(
            commits=[
                CommitInfo(
                    sha="a",
                    message="update",
                    author_name="A",
                    author_email="a@t.com",
                    author_date="2026-01-01T00:00:00Z",
                    committer_name="A",
                    committer_date="2026-01-01T00:00:00Z",
                ),
                CommitInfo(
                    sha="b",
                    message="fix",
                    author_name="A",
                    author_email="a@t.com",
                    author_date="2026-01-02T00:00:00Z",
                    committer_name="A",
                    committer_date="2026-01-02T00:00:00Z",
                ),
                CommitInfo(
                    sha="c",
                    message="asdf",
                    author_name="A",
                    author_email="a@t.com",
                    author_date="2026-01-03T00:00:00Z",
                    committer_name="A",
                    committer_date="2026-01-03T00:00:00Z",
                ),
            ]
        )
        result = GIT_HYGIENE_RULES[0].evaluate(data)
        assert result.passed is False

    def test_commit_frequency_pass(self) -> None:
        commits = [
            CommitInfo(
                sha=f"c{i}",
                message=f"Commit {i}",
                author_name="A",
                author_email="a@t.com",
                author_date="2026-01-01T00:00:00Z",
                committer_name="A",
                committer_date="2026-01-01T00:00:00Z",
            )
            for i in range(15)
        ]
        data = _make_data(commits=commits)
        result = GIT_HYGIENE_RULES[1].evaluate(data)
        assert result.passed is True

    def test_commit_frequency_fail(self) -> None:
        data = _make_data(
            commits=[
                CommitInfo(
                    sha="a",
                    message="init",
                    author_name="A",
                    author_email="a@t.com",
                    author_date="2026-01-01T00:00:00Z",
                    committer_name="A",
                    committer_date="2026-01-01T00:00:00Z",
                ),
            ]
        )
        result = GIT_HYGIENE_RULES[1].evaluate(data)
        assert result.passed is False

    def test_contributor_activity_pass(self) -> None:
        data = _make_data(
            commits=[
                CommitInfo(
                    sha="a",
                    message="First commit",
                    author_name="Alice",
                    author_email="a@t.com",
                    author_date="2026-01-01T00:00:00Z",
                    committer_name="Alice",
                    committer_date="2026-01-01T00:00:00Z",
                ),
                CommitInfo(
                    sha="b",
                    message="Second commit",
                    author_name="Bob",
                    author_email="b@t.com",
                    author_date="2026-01-02T00:00:00Z",
                    committer_name="Bob",
                    committer_date="2026-01-02T00:00:00Z",
                ),
            ]
        )
        result = GIT_HYGIENE_RULES[2].evaluate(data)
        assert result.passed is True


class TestLicensingRules:
    def test_license_file_pass(self) -> None:
        data = _make_data(
            tree=[
                TreeNode(
                    path="LICENSE",
                    mode="100644",
                    type="blob",
                    sha="a",
                    size=200,
                    url="",
                ),
            ]
        )
        result = LICENSING_RULES[0].evaluate(data)
        assert result.passed is True

    def test_license_file_fail(self) -> None:
        data = _make_data(tree=[])
        result = LICENSING_RULES[0].evaluate(data)
        assert result.passed is False

    def test_license_type_pass(self) -> None:
        data = _make_data(
            license=LicenseInfo(spdx_id="MIT", name="MIT License"),
        )
        result = LICENSING_RULES[1].evaluate(data)
        assert result.passed is True

    def test_license_type_fail(self) -> None:
        data = _make_data(license=None, tree=[])
        result = LICENSING_RULES[1].evaluate(data)
        assert result.passed is False


class TestSecurityRules:
    def test_gitignore_pass(self) -> None:
        data = _make_data(has_gitignore=True)
        result = SECURITY_RULES[0].evaluate(data)
        assert result.passed is True

    def test_gitignore_fail(self) -> None:
        data = _make_data(has_gitignore=False)
        result = SECURITY_RULES[0].evaluate(data)
        assert result.passed is False

    def test_secret_patterns_pass(self) -> None:
        data = _make_data(
            tree=[
                TreeNode(
                    path="src/main.py",
                    mode="100644",
                    type="blob",
                    sha="a",
                    size=100,
                    url="",
                ),
            ]
        )
        result = SECURITY_RULES[2].evaluate(data)
        assert result.passed is True

    def test_secret_patterns_fail(self) -> None:
        data = _make_data(
            tree=[
                TreeNode(path=".env", mode="100644", type="blob", sha="a", size=100, url=""),
            ]
        )
        result = SECURITY_RULES[2].evaluate(data)
        assert result.passed is False

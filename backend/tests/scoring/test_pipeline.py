from app.github.schemas import (
    CommitInfo,
    GitHubRepositoryData,
    LicenseInfo,
    ReleaseInfo,
    RepositoryInfo,
    TreeNode,
    WorkflowFile,
)
from app.scoring.pipeline import calculate_grade, run_scoring

DEFAULT_README = "# Test\n\n## Installation\n\npip install test\n\n## Usage\n\nimport test\n\n## License\n\nMIT"


def _make_repo(**kwargs: object) -> GitHubRepositoryData:
    defaults: dict[str, object] = {
        "repo": RepositoryInfo(
            full_name="test/repo",
            name="repo",
            owner="test",
            description="Test repo",
            default_branch="main",
            created_at="2026-01-01T00:00:00Z",
            updated_at="2026-07-01T00:00:00Z",
            pushed_at="2026-07-01T00:00:00Z",
            stargazers_count=100,
            forks_count=20,
            open_issues_count=5,
            language="Python",
            topics=[],
        ),
        "readme": DEFAULT_README,
        "tree": [],
        "commits": [
            CommitInfo(
                sha="abc123",
                message="Add initial implementation",
                author_name="Alice",
                author_email="alice@test.com",
                author_date="2026-01-01T00:00:00Z",
                committer_name="Alice",
                committer_date="2026-01-01T00:00:00Z",
            ),
        ],
        "workflows": [],
        "license": None,
        "has_gitignore": False,
        "has_dockerfile": False,
    }
    defaults.update(kwargs)
    return GitHubRepositoryData(**defaults)  # type: ignore[arg-type]


class TestCalculateGrade:
    def test_grade_a(self) -> None:
        assert calculate_grade(95) == "A"
        assert calculate_grade(90) == "A"

    def test_grade_b(self) -> None:
        assert calculate_grade(85) == "B"
        assert calculate_grade(80) == "B"

    def test_grade_c(self) -> None:
        assert calculate_grade(75) == "C"
        assert calculate_grade(70) == "C"

    def test_grade_d(self) -> None:
        assert calculate_grade(65) == "D"
        assert calculate_grade(60) == "D"

    def test_grade_f(self) -> None:
        assert calculate_grade(50) == "F"
        assert calculate_grade(0) == "F"


class TestRunScoring:
    def test_perfect_repo(self) -> None:
        readme = "# Great Project\n\n## Installation\n\nnpm install\n\n## Usage\n\nRun it\n\n## License\n\nMIT"
        data = _make_repo(
            readme=readme,
            tree=[
                TreeNode(
                    path="README.md",
                    mode="100644",
                    type="blob",
                    sha="a",
                    size=500,
                    url="",
                ),
                TreeNode(
                    path=".gitignore",
                    mode="100644",
                    type="blob",
                    sha="b",
                    size=100,
                    url="",
                ),
                TreeNode(
                    path="LICENSE",
                    mode="100644",
                    type="blob",
                    sha="c",
                    size=200,
                    url="",
                ),
                TreeNode(
                    path="CONTRIBUTING.md",
                    mode="100644",
                    type="blob",
                    sha="c2",
                    size=200,
                    url="",
                ),
                TreeNode(
                    path="CODE_OF_CONDUCT.md",
                    mode="100644",
                    type="blob",
                    sha="c3",
                    size=200,
                    url="",
                ),
                TreeNode(
                    path="CHANGELOG.md",
                    mode="100644",
                    type="blob",
                    sha="c4",
                    size=200,
                    url="",
                ),
                TreeNode(
                    path="tests/test_main.py",
                    mode="100644",
                    type="blob",
                    sha="d",
                    size=300,
                    url="",
                ),
                TreeNode(
                    path="conftest.py",
                    mode="100644",
                    type="blob",
                    sha="d2",
                    size=100,
                    url="",
                ),
                TreeNode(
                    path="pyproject.toml",
                    mode="100644",
                    type="blob",
                    sha="e",
                    size=400,
                    url="",
                ),
                TreeNode(
                    path=".coveragerc",
                    mode="100644",
                    type="blob",
                    sha="f",
                    size=50,
                    url="",
                ),
                TreeNode(
                    path="SECURITY.md",
                    mode="100644",
                    type="blob",
                    sha="g",
                    size=100,
                    url="",
                ),
                TreeNode(
                    path=".github/dependabot.yml",
                    mode="100644",
                    type="blob",
                    sha="h",
                    size=100,
                    url="",
                ),
                TreeNode(
                    path="CODEOWNERS",
                    mode="100644",
                    type="blob",
                    sha="i",
                    size=50,
                    url="",
                ),
                TreeNode(
                    path=".github/pull_request_template.md",
                    mode="100644",
                    type="blob",
                    sha="j",
                    size=100,
                    url="",
                ),
                TreeNode(
                    path=".github/ISSUE_TEMPLATE.md",
                    mode="100644",
                    type="blob",
                    sha="k",
                    size=100,
                    url="",
                ),
                TreeNode(
                    path=".github/secret-scanning.yml",
                    mode="100644",
                    type="blob",
                    sha="l",
                    size=50,
                    url="",
                ),
                TreeNode(
                    path="src/main.py",
                    mode="100644",
                    type="blob",
                    sha="m",
                    size=500,
                    url="",
                ),
            ],
            commits=[
                CommitInfo(
                    sha="a1",
                    message="Add feature A with comprehensive tests",
                    author_name="Alice",
                    author_email="a@t.com",
                    author_date="2026-01-01T00:00:00Z",
                    committer_name="Alice",
                    committer_date="2026-01-01T00:00:00Z",
                ),
                CommitInfo(
                    sha="a2",
                    message="Fix bug in feature B with regression test",
                    author_name="Bob",
                    author_email="b@t.com",
                    author_date="2026-01-02T00:00:00Z",
                    committer_name="Bob",
                    committer_date="2026-01-02T00:00:00Z",
                ),
                CommitInfo(
                    sha="a3",
                    message="Update documentation with examples",
                    author_name="Alice",
                    author_email="a@t.com",
                    author_date="2026-01-03T00:00:00Z",
                    committer_name="Alice",
                    committer_date="2026-01-03T00:00:00Z",
                ),
                CommitInfo(
                    sha="a4",
                    message="Refactor authentication module",
                    author_name="Bob",
                    author_email="b@t.com",
                    author_date="2026-01-04T00:00:00Z",
                    committer_name="Bob",
                    committer_date="2026-01-04T00:00:00Z",
                ),
                CommitInfo(
                    sha="a5",
                    message="Add CI/CD pipeline configuration",
                    author_name="Alice",
                    author_email="a@t.com",
                    author_date="2026-01-05T00:00:00Z",
                    committer_name="Alice",
                    committer_date="2026-01-05T00:00:00Z",
                ),
            ],
            workflows=[
                WorkflowFile(path=".github/workflows/ci.yml", name="CI", state="active"),
                WorkflowFile(path=".github/workflows/test.yml", name="Tests", state="active"),
                WorkflowFile(path=".github/workflows/lint.yml", name="Lint", state="active"),
                WorkflowFile(path=".github/workflows/deploy.yml", name="Deploy", state="active"),
                WorkflowFile(path=".github/workflows/codeql-analysis.yml", name="CodeQL", state="active"),
            ],
            license=LicenseInfo(spdx_id="MIT", name="MIT License"),
            has_gitignore=True,
            has_dockerfile=True,
            releases=[ReleaseInfo(tag_name="v1.0.0", name="Release 1.0.0")],
        )

        result = run_scoring(data)
        assert result.overall_score >= 80
        assert result.grade in ("A", "B")
        assert len(result.rules) > 0

    def test_empty_repo(self) -> None:
        data = _make_repo(
            readme=None,
            tree=[],
            commits=[],
            workflows=[],
            license=None,
            has_gitignore=False,
            has_dockerfile=False,
        )

        result = run_scoring(data)
        assert result.overall_score <= 30
        assert result.grade == "F"

    def test_deterministic_output(self) -> None:
        data = _make_repo()
        result1 = run_scoring(data)
        result2 = run_scoring(data)
        assert result1.overall_score == result2.overall_score
        assert result1.grade == result2.grade
        assert len(result1.rules) == len(result2.rules)

    def test_all_rules_returned(self) -> None:
        data = _make_repo()
        result = run_scoring(data)
        assert len(result.rules) >= 20

    def test_categories_cover_all(self) -> None:
        data = _make_repo()
        result = run_scoring(data)
        cat_names = {c.name for c in result.categories}
        expected = {
            "Testing",
            "CI/CD",
            "Documentation",
            "Git Hygiene",
            "Licensing",
            "Security",
        }
        assert cat_names == expected

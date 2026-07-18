from app.api.report_service import compute_summary
from app.github.schemas import (
    CommitInfo,
    GitHubRepositoryData,
    RepositoryInfo,
)
from app.scoring.pipeline import run_scoring


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


class TestSummaryCalculation:
    def test_summary_from_perfect_repo(self) -> None:
        readme = "# Great Project\n\n## Installation\n\nnpm install\n\n## Usage\n\nRun it\n\n## License\n\nMIT"
        data = _make_data(
            readme=readme,
            tree=[
                {"path": "README.md", "mode": "100644", "type": "blob", "sha": "a", "size": 500, "url": ""},
                {"path": ".gitignore", "mode": "100644", "type": "blob", "sha": "b", "size": 100, "url": ""},
                {"path": "LICENSE", "mode": "100644", "type": "blob", "sha": "c", "size": 200, "url": ""},
                {"path": "tests/test_main.py", "mode": "100644", "type": "blob", "sha": "d", "size": 300, "url": ""},
                {"path": ".coveragerc", "mode": "100644", "type": "blob", "sha": "e", "size": 50, "url": ""},
                {"path": "SECURITY.md", "mode": "100644", "type": "blob", "sha": "f", "size": 100, "url": ""},
                {
                    "path": ".github/dependabot.yml",
                    "mode": "100644",
                    "type": "blob",
                    "sha": "g",
                    "size": 100,
                    "url": "",
                },
                {
                    "path": ".github/workflows/ci.yml",
                    "mode": "100644",
                    "type": "blob",
                    "sha": "h",
                    "size": 100,
                    "url": "",
                },
                {
                    "path": ".github/workflows/test.yml",
                    "mode": "100644",
                    "type": "blob",
                    "sha": "i",
                    "size": 100,
                    "url": "",
                },
                {
                    "path": ".github/workflows/lint.yml",
                    "mode": "100644",
                    "type": "blob",
                    "sha": "j",
                    "size": 100,
                    "url": "",
                },
                {
                    "path": ".github/workflows/deploy.yml",
                    "mode": "100644",
                    "type": "blob",
                    "sha": "k",
                    "size": 100,
                    "url": "",
                },
            ],
            commits=[
                CommitInfo(
                    sha=f"c{i}",
                    message=f"Meaningful commit {i} with details",
                    author_name="Alice" if i % 2 == 0 else "Bob",
                    author_email="a@t.com",
                    author_date="2026-01-01T00:00:00Z",
                    committer_name="Alice",
                    committer_date="2026-01-01T00:00:00Z",
                )
                for i in range(12)
            ],
            workflows=[
                {"path": ".github/workflows/ci.yml", "name": "CI", "state": "active"},
                {"path": ".github/workflows/test.yml", "name": "Tests", "state": "active"},
                {"path": ".github/workflows/lint.yml", "name": "Lint", "state": "active"},
                {"path": ".github/workflows/deploy.yml", "name": "Deploy", "state": "active"},
            ],
            has_gitignore=True,
        )
        from app.github.schemas import LicenseInfo, TreeNode, WorkflowFile

        tree_items = [
            TreeNode(path="README.md", mode="100644", type="blob", sha="a", size=500, url=""),
            TreeNode(path=".gitignore", mode="100644", type="blob", sha="b", size=100, url=""),
            TreeNode(path="LICENSE", mode="100644", type="blob", sha="c", size=200, url=""),
            TreeNode(path="tests/test_main.py", mode="100644", type="blob", sha="d", size=300, url=""),
            TreeNode(path=".coveragerc", mode="100644", type="blob", sha="e", size=50, url=""),
            TreeNode(path="SECURITY.md", mode="100644", type="blob", sha="f", size=100, url=""),
            TreeNode(path=".github/dependabot.yml", mode="100644", type="blob", sha="g", size=100, url=""),
        ]
        data = _make_data(
            readme=readme,
            tree=tree_items,
            commits=[
                CommitInfo(
                    sha=f"c{i}",
                    message=f"Meaningful commit {i} with details",
                    author_name="Alice" if i % 2 == 0 else "Bob",
                    author_email="a@t.com",
                    author_date="2026-01-01T00:00:00Z",
                    committer_name="Alice",
                    committer_date="2026-01-01T00:00:00Z",
                )
                for i in range(12)
            ],
            workflows=[
                WorkflowFile(path=".github/workflows/ci.yml", name="CI", state="active"),
                WorkflowFile(path=".github/workflows/test.yml", name="Tests", state="active"),
                WorkflowFile(path=".github/workflows/lint.yml", name="Lint", state="active"),
                WorkflowFile(path=".github/workflows/deploy.yml", name="Deploy", state="active"),
            ],
            license=LicenseInfo(spdx_id="MIT", name="MIT License"),
            has_gitignore=True,
        )

        result = run_scoring(data)
        summary = compute_summary(result)

        assert summary["overall_percentage"] == result.overall_score
        assert summary["grade"] == result.grade
        assert summary["passed_rules"] + summary["failed_rules"] == summary["total_rules"]
        assert summary["total_rules"] > 0
        assert summary["categories_passed"] + summary["categories_failed"] == 6

    def test_summary_from_empty_repo(self) -> None:
        data = _make_data()
        result = run_scoring(data)
        summary = compute_summary(result)

        assert summary["overall_percentage"] <= 30
        assert summary["grade"] == "F"
        assert summary["failed_rules"] > 0
        assert summary["total_rules"] > 0

    def test_summary_total_matches_rules(self) -> None:
        data = _make_data()
        result = run_scoring(data)
        summary = compute_summary(result)

        assert summary["total_rules"] == len(result.rules)
        assert summary["passed_rules"] + summary["failed_rules"] == summary["total_rules"]

    def test_summary_grade_matches(self) -> None:
        data = _make_data()
        result = run_scoring(data)
        summary = compute_summary(result)

        assert summary["grade"] == result.grade

    def test_summary_percentage_matches(self) -> None:
        data = _make_data()
        result = run_scoring(data)
        summary = compute_summary(result)

        assert summary["overall_percentage"] == result.overall_score

    def test_summary_categories_count(self) -> None:
        data = _make_data()
        result = run_scoring(data)
        summary = compute_summary(result)

        assert summary["categories_passed"] + summary["categories_failed"] == 6
        assert summary["categories_passed"] >= 0
        assert summary["categories_failed"] >= 0

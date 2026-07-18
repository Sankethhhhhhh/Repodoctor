"""Regression tests for scoring engine — ensures specific repo shapes produce expected scores."""

from app.github.schemas import (
    CommitInfo,
    GitHubRepositoryData,
    LicenseInfo,
    ReleaseInfo,
    RepositoryInfo,
    TreeNode,
    WorkflowFile,
)
from app.scoring.pipeline import run_scoring


def _commit(sha: str = "a", message: str = "Add feature", author: str = "Alice") -> CommitInfo:
    return CommitInfo(
        sha=sha,
        message=message,
        author_name=author,
        author_email=f"{author.lower()}@test.com",
        author_date="2026-01-01T00:00:00Z",
        committer_name=author,
        committer_date="2026-01-01T00:00:00Z",
    )


def _tree_node(path: str, size: int = 100, node_type: str = "blob") -> TreeNode:
    return TreeNode(
        path=path, mode="100644" if node_type == "blob" else "040000", type=node_type, sha="a", size=size, url=""
    )


def _workflow(path: str, name: str = "CI", state: str = "active") -> WorkflowFile:
    return WorkflowFile(path=f".github/workflows/{path}", name=name, state=state)


def _dir(path: str) -> TreeNode:
    return TreeNode(path=path, mode="040000", type="tree", sha="a", size=None, url="")


def _repo(**kwargs: object) -> GitHubRepositoryData:
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
        "readme": "# Test\n\n## Installation\n\npip install test\n\n## Usage\n\nimport test\n\n## License\n\nMIT",
        "tree": [],
        "commits": [_commit()],
        "workflows": [],
        "license": None,
        "has_gitignore": False,
        "has_dockerfile": False,
        "releases": [],
    }
    defaults.update(kwargs)
    return GitHubRepositoryData(**defaults)  # type: ignore[arg-type]


def _get_rule(scoring_result, rule_id: str):
    for cat in scoring_result.categories:
        for d in cat.details:
            if d["rule"] == rule_id:
                return d
    return None


def _get_cat_score(scoring_result, cat_name: str):
    for cat in scoring_result.categories:
        if cat.name == cat_name:
            return cat
    return None


# ── LICENSE scenarios ──────────────────────────────────────────────
class TestMissingLicense:
    def test_no_license_file_fails(self) -> None:
        data = _repo(tree=[_tree_node("README.md", 500)])
        result = run_scoring(data)
        rule = _get_rule(result, "LICENSE_FILE")
        assert rule is not None
        assert rule["status"] == "FAIL"

    def test_with_license_file_passes(self) -> None:
        data = _repo(
            tree=[_tree_node("LICENSE", 200)],
            license=LicenseInfo(spdx_id="MIT", name="MIT License"),
        )
        result = run_scoring(data)
        rule = _get_rule(result, "LICENSE_FILE")
        assert rule is not None
        assert rule["status"] == "PASS"

    def test_license_type_with_spdx_passes(self) -> None:
        data = _repo(license=LicenseInfo(spdx_id="Apache-2.0", name="Apache 2.0"))
        result = run_scoring(data)
        rule = _get_rule(result, "LICENSE_TYPE")
        assert rule is not None
        assert rule["status"] == "PASS"

    def test_license_type_without_spdx_fails(self) -> None:
        data = _repo(license=LicenseInfo(spdx_id=None, name="Custom License"))
        result = run_scoring(data)
        rule = _get_rule(result, "LICENSE_TYPE")
        assert rule is not None
        assert rule["status"] == "FAIL"

    def test_license_type_none_fails(self) -> None:
        data = _repo(license=None)
        result = run_scoring(data)
        rule = _get_rule(result, "LICENSE_TYPE")
        assert rule is not None
        assert rule["status"] == "FAIL"

    def test_lowercase_license_file_passes(self) -> None:
        """next.js uses lowercase license.md."""
        data = _repo(tree=[_tree_node("license.md", 200)])
        result = run_scoring(data)
        rule = _get_rule(result, "LICENSE_FILE")
        assert rule is not None
        assert rule["status"] == "PASS"

    def test_license_txt_passes(self) -> None:
        """vscode uses LICENSE.txt."""
        data = _repo(tree=[_tree_node("LICENSE.txt", 200)])
        result = run_scoring(data)
        rule = _get_rule(result, "LICENSE_FILE")
        assert rule is not None
        assert rule["status"] == "PASS"


# ── README scenarios ──────────────────────────────────────────────
class TestMissingReadme:
    def test_no_readme_fails(self) -> None:
        data = _repo(readme=None)
        result = run_scoring(data)
        rule = _get_rule(result, "README_EXISTS")
        assert rule is not None
        assert rule["status"] == "FAIL"

    def test_readme_too_short_fails(self) -> None:
        data = _repo(readme="Hi")
        result = run_scoring(data)
        rule = _get_rule(result, "README_LENGTH")
        assert rule is not None
        assert rule["status"] == "FAIL"

    def test_readme_with_sections_passes(self) -> None:
        readme = "# Project\n\n## Installation\n\npip install foo\n\n## Usage\n\nRun it\n\n## License\n\nMIT"
        data = _repo(readme=readme)
        result = run_scoring(data)
        rule = _get_rule(result, "README_SECTIONS")
        assert rule is not None
        assert rule["status"] == "PASS"

    def test_readme_with_two_of_three_sections_passes(self) -> None:
        """README with only Installation and Usage (no License section) should still pass."""
        readme = "# Project\n\n## Installation\n\npip install foo\n\n## Usage\n\nRun it"
        data = _repo(readme=readme)
        result = run_scoring(data)
        rule = _get_rule(result, "README_SECTIONS")
        assert rule is not None
        assert rule["status"] == "PASS"

    def test_readme_with_one_section_fails(self) -> None:
        """README with only one section should fail."""
        readme = "# Project\n\n## Installation\n\npip install foo"
        data = _repo(readme=readme)
        result = run_scoring(data)
        rule = _get_rule(result, "README_SECTIONS")
        assert rule is not None
        assert rule["status"] == "FAIL"


# ── CONTRIBUTING / CODE_OF_CONDUCT ─────────────────────────────────
class TestCommunityFiles:
    def test_contributing_absent_fails(self) -> None:
        data = _repo()
        result = run_scoring(data)
        rule = _get_rule(result, "CONTRIBUTING_EXISTS")
        assert rule is not None
        assert rule["status"] == "FAIL"

    def test_contributing_present_passes(self) -> None:
        data = _repo(tree=[_tree_node("CONTRIBUTING.md")])
        result = run_scoring(data)
        rule = _get_rule(result, "CONTRIBUTING_EXISTS")
        assert rule is not None
        assert rule["status"] == "PASS"

    def test_contributing_lowercase_passes(self) -> None:
        """next.js uses lowercase contributing.md."""
        data = _repo(tree=[_tree_node("contributing.md")])
        result = run_scoring(data)
        rule = _get_rule(result, "CONTRIBUTING_EXISTS")
        assert rule is not None
        assert rule["status"] == "PASS"

    def test_contributing_rst_in_github_passes(self) -> None:
        """cpython uses .github/CONTRIBUTING.rst."""
        data = _repo(tree=[_tree_node(".github/CONTRIBUTING.rst")])
        result = run_scoring(data)
        rule = _get_rule(result, "CONTRIBUTING_EXISTS")
        assert rule is not None
        assert rule["status"] == "PASS"

    def test_code_of_conduct_absent_fails(self) -> None:
        data = _repo()
        result = run_scoring(data)
        rule = _get_rule(result, "CODE_OF_CONDUCT")
        assert rule is not None
        assert rule["status"] == "FAIL"

    def test_code_of_conduct_present_passes(self) -> None:
        data = _repo(tree=[_tree_node("CODE_OF_CONDUCT.md")])
        result = run_scoring(data)
        rule = _get_rule(result, "CODE_OF_CONDUCT")
        assert rule is not None
        assert rule["status"] == "PASS"

    def test_code_of_conduct_hyphenated_passes(self) -> None:
        """kubernetes uses code-of-conduct.md."""
        data = _repo(tree=[_tree_node("code-of-conduct.md")])
        result = run_scoring(data)
        rule = _get_rule(result, "CODE_OF_CONDUCT")
        assert rule is not None
        assert rule["status"] == "PASS"

    def test_changelog_absent_fails(self) -> None:
        data = _repo()
        result = run_scoring(data)
        rule = _get_rule(result, "CHANGELOG_EXISTS")
        assert rule is not None
        assert rule["status"] == "FAIL"

    def test_changelog_present_passes(self) -> None:
        data = _repo(tree=[_tree_node("CHANGELOG.md")])
        result = run_scoring(data)
        rule = _get_rule(result, "CHANGELOG_EXISTS")
        assert rule is not None
        assert rule["status"] == "PASS"

    def test_releases_as_changelog_passes(self) -> None:
        """Repos with 3+ releases but no CHANGELOG file should pass (releases serve as changelog)."""
        data = _repo(
            releases=[
                ReleaseInfo(tag_name="v3.0.0"),
                ReleaseInfo(tag_name="v2.1.0"),
                ReleaseInfo(tag_name="v2.0.0"),
            ]
        )
        result = run_scoring(data)
        rule = _get_rule(result, "CHANGELOG_EXISTS")
        assert rule is not None
        assert rule["status"] == "PASS"

    def test_few_releases_no_changelog_fails(self) -> None:
        """Repos with fewer than 3 releases and no CHANGELOG should fail."""
        data = _repo(releases=[ReleaseInfo(tag_name="v1.0.0")])
        result = run_scoring(data)
        rule = _get_rule(result, "CHANGELOG_EXISTS")
        assert rule is not None
        assert rule["status"] == "FAIL"


# ── DOCS_DIRECTORY ────────────────────────────────────────────────
class TestDocsDirectory:
    def test_docs_dir_passes(self) -> None:
        data = _repo(tree=[_dir("docs"), _tree_node("docs/index.md")])
        result = run_scoring(data)
        rule = _get_rule(result, "DOCS_DIRECTORY")
        assert rule is not None
        assert rule["status"] == "PASS"

    def test_doc_dir_passes(self) -> None:
        """cpython uses Doc/ directory."""
        data = _repo(tree=[_dir("Doc"), _tree_node("Doc/library.rst")])
        result = run_scoring(data)
        rule = _get_rule(result, "DOCS_DIRECTORY")
        assert rule is not None
        assert rule["status"] == "PASS"

    def test_no_docs_dir_fails(self) -> None:
        data = _repo(tree=[_tree_node("src/main.py")])
        result = run_scoring(data)
        rule = _get_rule(result, "DOCS_DIRECTORY")
        assert rule is not None
        assert rule["status"] == "FAIL"

    def test_website_dir_passes(self) -> None:
        data = _repo(tree=[_dir("website"), _tree_node("website/index.html")])
        result = run_scoring(data)
        rule = _get_rule(result, "DOCS_DIRECTORY")
        assert rule is not None
        assert rule["status"] == "PASS"


# ── CI/CD scenarios ──────────────────────────────────────────────
class TestCIScenarios:
    def test_no_ci_fails_github_actions(self) -> None:
        data = _repo(workflows=[])
        result = run_scoring(data)
        rule = _get_rule(result, "GITHUB_ACTIONS")
        assert rule is not None
        assert rule["status"] == "FAIL"

    def test_single_workflow_passes_github_actions(self) -> None:
        data = _repo(workflows=[_workflow("ci.yml")])
        result = run_scoring(data)
        rule = _get_rule(result, "GITHUB_ACTIONS")
        assert rule is not None
        assert rule["status"] == "PASS"

    def test_build_workflow_detected(self) -> None:
        data = _repo(workflows=[_workflow("build.yml", "Build")])
        result = run_scoring(data)
        rule = _get_rule(result, "BUILD_WORKFLOW")
        assert rule is not None
        assert rule["status"] == "PASS"

    def test_lint_workflow_detected(self) -> None:
        data = _repo(workflows=[_workflow("lint.yml", "Lint")])
        result = run_scoring(data)
        rule = _get_rule(result, "LINT_WORKFLOW")
        assert rule is not None
        assert rule["status"] == "PASS"

    def test_deploy_workflow_detected(self) -> None:
        data = _repo(workflows=[_workflow("deploy.yml", "Deploy")])
        result = run_scoring(data)
        rule = _get_rule(result, "DEPLOY_WORKFLOW")
        assert rule is not None
        assert rule["status"] == "PASS"

    def test_ci_test_workflow_detected(self) -> None:
        data = _repo(workflows=[_workflow("test.yml", "Tests")])
        result = run_scoring(data)
        rule = _get_rule(result, "CI_TEST_WORKFLOW")
        assert rule is not None
        assert rule["status"] == "PASS"

    def test_pr_workflow_passes_build(self) -> None:
        """vscode-style workflow named pr.yml should be detected as build/CI."""
        data = _repo(workflows=[_workflow("pr.yml", "PR Checks")])
        result = run_scoring(data)
        rule = _get_rule(result, "BUILD_WORKFLOW")
        assert rule is not None
        assert rule["status"] == "PASS"

    def test_validate_workflow_passes_lint(self) -> None:
        """A workflow named 'Validate' should be detected as lint/quality."""
        data = _repo(workflows=[_workflow("validate.yml", "Validate")])
        result = run_scoring(data)
        rule = _get_rule(result, "LINT_WORKFLOW")
        assert rule is not None
        assert rule["status"] == "PASS"

    def test_typecheck_workflow_passes_lint(self) -> None:
        """A workflow named 'TypeCheck' should be detected as lint/quality."""
        data = _repo(workflows=[_workflow("typecheck.yml", "TypeCheck")])
        result = run_scoring(data)
        rule = _get_rule(result, "LINT_WORKFLOW")
        assert rule is not None
        assert rule["status"] == "PASS"

    def test_release_workflow_passes_deploy(self) -> None:
        """A workflow named 'release' should be detected as deploy."""
        data = _repo(workflows=[_workflow("release.yml", "Release")])
        result = run_scoring(data)
        rule = _get_rule(result, "DEPLOY_WORKFLOW")
        assert rule is not None
        assert rule["status"] == "PASS"

    def test_build_and_test_passes_build(self) -> None:
        """next.js-style workflow named build_and_test.yml should pass build."""
        data = _repo(workflows=[_workflow("build_and_test.yml", "Build and Test")])
        result = run_scoring(data)
        rule = _get_rule(result, "BUILD_WORKFLOW")
        assert rule is not None
        assert rule["status"] == "PASS"

    def test_any_workflow_passes_build(self) -> None:
        """If workflows exist but none match keywords, build still passes (workflows configured)."""
        data = _repo(workflows=[_workflow("mystery.yml", "Mystery")])
        result = run_scoring(data)
        rule = _get_rule(result, "BUILD_WORKFLOW")
        assert rule is not None
        assert rule["status"] == "PASS"


# ── Security scenarios ────────────────────────────────────────────
class TestSecurityScenarios:
    def test_no_gitignore_fails(self) -> None:
        data = _repo(has_gitignore=False)
        result = run_scoring(data)
        rule = _get_rule(result, "GITIGNORE_EXISTS")
        assert rule is not None
        assert rule["status"] == "FAIL"

    def test_gitignore_present_passes(self) -> None:
        data = _repo(has_gitignore=True)
        result = run_scoring(data)
        rule = _get_rule(result, "GITIGNORE_EXISTS")
        assert rule is not None
        assert rule["status"] == "PASS"

    def test_no_security_policy_fails(self) -> None:
        data = _repo()
        result = run_scoring(data)
        rule = _get_rule(result, "SECURITY_POLICY")
        assert rule is not None
        assert rule["status"] == "FAIL"

    def test_security_policy_present_passes(self) -> None:
        data = _repo(tree=[_tree_node("SECURITY.md")])
        result = run_scoring(data)
        rule = _get_rule(result, "SECURITY_POLICY")
        assert rule is not None
        assert rule["status"] == "PASS"

    def test_security_in_github_dir_passes(self) -> None:
        """cpython uses .github/SECURITY.md."""
        data = _repo(tree=[_tree_node(".github/SECURITY.md")])
        result = run_scoring(data)
        rule = _get_rule(result, "SECURITY_POLICY")
        assert rule is not None
        assert rule["status"] == "PASS"

    def test_security_contacts_passes(self) -> None:
        """kubernetes uses SECURITY_CONTACTS."""
        data = _repo(tree=[_tree_node("SECURITY_CONTACTS")])
        result = run_scoring(data)
        rule = _get_rule(result, "SECURITY_POLICY")
        assert rule is not None
        assert rule["status"] == "PASS"

    def test_no_dependabot_fails(self) -> None:
        data = _repo()
        result = run_scoring(data)
        rule = _get_rule(result, "DEPENDABOT")
        assert rule is not None
        assert rule["status"] == "FAIL"

    def test_dependabot_present_passes(self) -> None:
        data = _repo(tree=[_tree_node(".github/dependabot.yml")])
        result = run_scoring(data)
        rule = _get_rule(result, "DEPENDABOT")
        assert rule is not None
        assert rule["status"] == "PASS"

    def test_renovate_present_passes(self) -> None:
        """Renovate should be accepted as alternative to Dependabot."""
        data = _repo(tree=[_tree_node("renovate.json")])
        result = run_scoring(data)
        rule = _get_rule(result, "DEPENDABOT")
        assert rule is not None
        assert rule["status"] == "PASS"

    def test_renovate_in_github_dir_passes(self) -> None:
        data = _repo(tree=[_tree_node(".github/renovate.json5")])
        result = run_scoring(data)
        rule = _get_rule(result, "DEPENDABOT")
        assert rule is not None
        assert rule["status"] == "PASS"

    def test_codeql_absent_fails(self) -> None:
        data = _repo()
        result = run_scoring(data)
        rule = _get_rule(result, "CODEQL_WORKFLOW")
        assert rule is not None
        assert rule["status"] == "FAIL"

    def test_codeql_present_passes(self) -> None:
        data = _repo(workflows=[_workflow("codeql-analysis.yml", "CodeQL")])
        result = run_scoring(data)
        rule = _get_rule(result, "CODEQL_WORKFLOW")
        assert rule is not None
        assert rule["status"] == "PASS"

    def test_secret_scanning_absent_fails(self) -> None:
        data = _repo()
        result = run_scoring(data)
        rule = _get_rule(result, "SECRET_SCANNING")
        assert rule is not None
        assert rule["status"] == "FAIL"

    def test_secret_scanning_present_passes(self) -> None:
        data = _repo(tree=[_tree_node(".github/secret-scanning.yml")])
        result = run_scoring(data)
        rule = _get_rule(result, "SECRET_SCANNING")
        assert rule is not None
        assert rule["status"] == "PASS"

    def test_env_in_test_dir_not_flagged(self) -> None:
        data = _repo(tree=[_tree_node("tests/test_apps/.env"), _tree_node("src/main.py")])
        result = run_scoring(data)
        rule = _get_rule(result, "SECRET_PATTERNS")
        assert rule is not None
        assert rule["status"] == "PASS"

    def test_pem_in_test_certs_not_flagged(self) -> None:
        data = _repo(tree=[_tree_node("tests/certs/ca.pem"), _tree_node("src/main.py")])
        result = run_scoring(data)
        rule = _get_rule(result, "SECRET_PATTERNS")
        assert rule is not None
        assert rule["status"] == "PASS"

    def test_env_at_root_still_flagged(self) -> None:
        data = _repo(tree=[_tree_node(".env"), _tree_node("src/main.py")])
        result = run_scoring(data)
        rule = _get_rule(result, "SECRET_PATTERNS")
        assert rule is not None
        assert rule["status"] == "FAIL"


# ── Test framework scenarios ──────────────────────────────────────
class TestFrameworkScenarios:
    def test_pytest_detected_via_conftest(self) -> None:
        data = _repo(tree=[_tree_node("conftest.py"), _tree_node("tests/test_main.py")])
        result = run_scoring(data)
        rule = _get_rule(result, "TEST_FRAMEWORK")
        assert rule is not None
        assert rule["status"] == "PASS"

    def test_jest_detected_via_config(self) -> None:
        data = _repo(tree=[_tree_node("jest.config.js"), _tree_node("tests/app.test.js")])
        result = run_scoring(data)
        rule = _get_rule(result, "TEST_FRAMEWORK")
        assert rule is not None
        assert rule["status"] == "PASS"

    def test_cargo_test_detected(self) -> None:
        data = _repo(tree=[_tree_node("Cargo.toml"), _tree_node("tests/integration.rs")])
        result = run_scoring(data)
        rule = _get_rule(result, "TEST_FRAMEWORK")
        assert rule is not None
        assert rule["status"] == "PASS"

    def test_coverage_config_present(self) -> None:
        data = _repo(tree=[_tree_node(".coveragerc")])
        result = run_scoring(data)
        rule = _get_rule(result, "COVERAGE_CONFIG")
        assert rule is not None
        assert rule["status"] == "PASS"

    def test_test_directory_present(self) -> None:
        data = _repo(tree=[_tree_node("tests/test_main.py")])
        result = run_scoring(data)
        rule = _get_rule(result, "TEST_DIRECTORY")
        assert rule is not None
        assert rule["status"] == "PASS"

    def test_no_tests_fails_all_testing_rules(self) -> None:
        data = _repo(tree=[])
        result = run_scoring(data)
        for rule_id in ["TEST_DIRECTORY", "TEST_FRAMEWORK", "CI_TEST_WORKFLOW"]:
            rule = _get_rule(result, rule_id)
            assert rule is not None
            assert rule["status"] == "FAIL", f"{rule_id} should fail with no tests"

    def test_pyproject_toml_with_test_files_detected(self) -> None:
        data = _repo(tree=[_tree_node("pyproject.toml"), _tree_node("tests/test_main.py")])
        result = run_scoring(data)
        rule = _get_rule(result, "TEST_FRAMEWORK")
        assert rule is not None
        assert rule["status"] == "PASS"

    def test_pyproject_toml_alone_not_detected(self) -> None:
        data = _repo(tree=[_tree_node("pyproject.toml"), _tree_node("src/main.py")])
        result = run_scoring(data)
        rule = _get_rule(result, "TEST_FRAMEWORK")
        assert rule is not None
        assert rule["status"] == "FAIL"

    def test_tsconfig_not_false_positive_for_coverage(self) -> None:
        """tsconfig.json should NOT trigger COVERAGE_CONFIG."""
        data = _repo(tree=[_tree_node("tsconfig.json"), _tree_node("src/main.ts")])
        result = run_scoring(data)
        rule = _get_rule(result, "COVERAGE_CONFIG")
        assert rule is not None
        assert rule["status"] == "FAIL"

    def test_phpunit_detected(self) -> None:
        data = _repo(tree=[_tree_node("phpunit.xml"), _tree_node("tests/Unit.php")])
        result = run_scoring(data)
        rule = _get_rule(result, "TEST_FRAMEWORK")
        assert rule is not None
        assert rule["status"] == "PASS"

    def test_playwright_detected(self) -> None:
        data = _repo(tree=[_tree_node("playwright.config.ts"), _tree_node("tests/e2e.spec.ts")])
        result = run_scoring(data)
        rule = _get_rule(result, "TEST_FRAMEWORK")
        assert rule is not None
        assert rule["status"] == "PASS"

    def test_jest_detected_via_tests_dir(self) -> None:
        """react uses __tests__ directory without a standard jest.config at root."""
        data = _repo(tree=[_dir("__tests__"), _tree_node("__tests__/app.test.js")])
        result = run_scoring(data)
        rule = _get_rule(result, "TEST_FRAMEWORK")
        assert rule is not None
        assert rule["status"] == "PASS"

    def test_python_unittest_detected_via_test_files(self) -> None:
        """cpython uses unittest with test_*.py files, no pyproject.toml."""
        data = _repo(
            tree=[
                _tree_node("Lib/test/test_os.py"),
                _tree_node("Lib/test/test_shutil.py"),
            ]
        )
        result = run_scoring(data)
        rule = _get_rule(result, "TEST_FRAMEWORK")
        assert rule is not None
        assert rule["status"] == "PASS"

    def test_python_unittest_detected_via_suffix(self) -> None:
        """test files ending in _test.py should also be detected."""
        data = _repo(
            tree=[
                _tree_node("tests/models_test.py"),
                _tree_node("tests/views_test.py"),
            ]
        )
        result = run_scoring(data)
        rule = _get_rule(result, "TEST_FRAMEWORK")
        assert rule is not None
        assert rule["status"] == "PASS"

    def test_secret_in_docs_dir_not_flagged(self) -> None:
        """cpython's Doc/library/secrets.rst should not be flagged."""
        data = _repo(tree=[_tree_node("Doc/library/secrets.rst"), _tree_node("src/main.py")])
        result = run_scoring(data)
        rule = _get_rule(result, "SECRET_PATTERNS")
        assert rule is not None
        assert rule["status"] == "PASS"

    def test_secret_in_lib_dir_not_flagged(self) -> None:
        """cpython's Lib/secrets.py should not be flagged."""
        data = _repo(tree=[_tree_node("Lib/secrets.py"), _tree_node("src/main.py")])
        result = run_scoring(data)
        rule = _get_rule(result, "SECRET_PATTERNS")
        assert rule is not None
        assert rule["status"] == "PASS"

    def test_env_in_fixtures_dir_not_flagged(self) -> None:
        """react's fixtures/ .env files should not be flagged."""
        data = _repo(tree=[_tree_node("fixtures/fiber-debugger/.env"), _tree_node("src/main.py")])
        result = run_scoring(data)
        rule = _get_rule(result, "SECRET_PATTERNS")
        assert rule is not None
        assert rule["status"] == "PASS"

    def test_secret_in_vendor_dir_not_flagged(self) -> None:
        data = _repo(tree=[_tree_node("vendor/secret.txt"), _tree_node("src/main.py")])
        result = run_scoring(data)
        rule = _get_rule(result, "SECRET_PATTERNS")
        assert rule is not None
        assert rule["status"] == "PASS"


# ── Git Hygiene scenarios ─────────────────────────────────────────
class TestGitHygieneScenarios:
    def test_codeowners_absent_fails(self) -> None:
        data = _repo()
        result = run_scoring(data)
        rule = _get_rule(result, "CODEOWNERS_EXISTS")
        assert rule is not None
        assert rule["status"] == "FAIL"

    def test_codeowners_present_passes(self) -> None:
        data = _repo(tree=[_tree_node("CODEOWNERS")])
        result = run_scoring(data)
        rule = _get_rule(result, "CODEOWNERS_EXISTS")
        assert rule is not None
        assert rule["status"] == "PASS"

    def test_owners_file_passes(self) -> None:
        """kubernetes uses OWNERS instead of CODEOWNERS."""
        data = _repo(tree=[_tree_node("OWNERS")])
        result = run_scoring(data)
        rule = _get_rule(result, "CODEOWNERS_EXISTS")
        assert rule is not None
        assert rule["status"] == "PASS"

    def test_pr_template_absent_fails(self) -> None:
        data = _repo()
        result = run_scoring(data)
        rule = _get_rule(result, "PR_TEMPLATE_EXISTS")
        assert rule is not None
        assert rule["status"] == "FAIL"

    def test_pr_template_present_passes(self) -> None:
        data = _repo(tree=[_tree_node(".github/pull_request_template.md")])
        result = run_scoring(data)
        rule = _get_rule(result, "PR_TEMPLATE_EXISTS")
        assert rule is not None
        assert rule["status"] == "PASS"

    def test_pr_template_uppercase_passes(self) -> None:
        """react uses PULL_REQUEST_TEMPLATE.md (uppercase)."""
        data = _repo(tree=[_tree_node(".github/PULL_REQUEST_TEMPLATE.md")])
        result = run_scoring(data)
        rule = _get_rule(result, "PR_TEMPLATE_EXISTS")
        assert rule is not None
        assert rule["status"] == "PASS"

    def test_issue_template_absent_fails(self) -> None:
        data = _repo()
        result = run_scoring(data)
        rule = _get_rule(result, "ISSUE_TEMPLATE_EXISTS")
        assert rule is not None
        assert rule["status"] == "FAIL"

    def test_issue_template_present_passes(self) -> None:
        data = _repo(tree=[_tree_node(".github/ISSUE_TEMPLATE.md")])
        result = run_scoring(data)
        rule = _get_rule(result, "ISSUE_TEMPLATE_EXISTS")
        assert rule is not None
        assert rule["status"] == "PASS"

    def test_issue_template_yaml_in_dir_passes(self) -> None:
        """Repos with YAML issue templates in .github/ISSUE_TEMPLATE/ should pass."""
        data = _repo(
            tree=[
                _dir(".github/ISSUE_TEMPLATE"),
                _tree_node(".github/ISSUE_TEMPLATE/bug_report.yml"),
                _tree_node(".github/ISSUE_TEMPLATE/config.yml"),
            ]
        )
        result = run_scoring(data)
        rule = _get_rule(result, "ISSUE_TEMPLATE_EXISTS")
        assert rule is not None
        assert rule["status"] == "PASS"

    def test_issue_template_file_in_dir_passes(self) -> None:
        """Repos with files directly under .github/ISSUE_TEMPLATE/ should pass."""
        data = _repo(
            tree=[
                _tree_node(".github/ISSUE_TEMPLATE/bug_report.md"),
            ]
        )
        result = run_scoring(data)
        rule = _get_rule(result, "ISSUE_TEMPLATE_EXISTS")
        assert rule is not None
        assert rule["status"] == "PASS"

    def test_releases_absent_fails(self) -> None:
        data = _repo()
        result = run_scoring(data)
        rule = _get_rule(result, "RELEASES_EXIST")
        assert rule is not None
        assert rule["status"] == "FAIL"

    def test_releases_present_passes(self) -> None:
        data = _repo(releases=[ReleaseInfo(tag_name="v1.0.0", name="Release 1.0.0")])
        result = run_scoring(data)
        rule = _get_rule(result, "RELEASES_EXIST")
        assert rule is not None
        assert rule["status"] == "PASS"


# ── Overall scoring scenarios ─────────────────────────────────────
class TestOverallScoring:
    def test_perfect_repo_scores_high(self) -> None:
        """A repo with everything should score >= 85."""
        result = _repo(
            readme="# Great Project\n\n## Installation\n\npip install foo\n\n## Usage\n\nRun it\n\n## License\n\nMIT",
            tree=[
                _tree_node("README.md", 500),
                _tree_node(".gitignore"),
                _tree_node("LICENSE", 200),
                _tree_node("CONTRIBUTING.md"),
                _tree_node("CODE_OF_CONDUCT.md"),
                _tree_node("CHANGELOG.md"),
                _tree_node("tests/test_main.py"),
                _tree_node("conftest.py"),
                _tree_node("pyproject.toml"),
                _tree_node(".coveragerc"),
                _tree_node("SECURITY.md"),
                _tree_node(".github/dependabot.yml"),
                _tree_node("CODEOWNERS"),
                _tree_node(".github/pull_request_template.md"),
                _tree_node(".github/ISSUE_TEMPLATE.md"),
                _tree_node(".github/secret-scanning.yml"),
                _tree_node("src/main.py", 500),
                _dir("docs"),
                _tree_node("docs/index.md"),
            ],
            commits=[
                _commit("a1", "Add feature A with comprehensive tests"),
                _commit("a2", "Fix bug in feature B", "Bob"),
                _commit("a3", "Update documentation with examples"),
                _commit("a4", "Refactor authentication module", "Bob"),
                _commit("a5", "Add CI/CD pipeline configuration"),
            ],
            workflows=[
                _workflow("ci.yml"),
                _workflow("test.yml", "Tests"),
                _workflow("lint.yml", "Lint"),
                _workflow("deploy.yml", "Deploy"),
                _workflow("codeql-analysis.yml", "CodeQL"),
            ],
            license=LicenseInfo(spdx_id="MIT", name="MIT License"),
            has_gitignore=True,
            has_dockerfile=True,
            releases=[ReleaseInfo(tag_name="v1.0.0", name="Release 1.0.0")],
        )
        result = run_scoring(result)
        assert result.overall_score >= 85, f"Expected >= 85, got {result.overall_score}"

    def test_bare_repo_scores_low(self) -> None:
        """A repo with nothing should score <= 20."""
        result = _repo(
            readme=None,
            tree=[],
            commits=[],
            workflows=[],
            license=None,
            has_gitignore=False,
            has_dockerfile=False,
            releases=[],
        )
        result = run_scoring(result)
        assert result.overall_score <= 20, f"Expected <= 20, got {result.overall_score}"

    def test_missing_license_penalizes_licensing_category(self) -> None:
        with_license = _repo(
            license=LicenseInfo(spdx_id="MIT", name="MIT License"),
            tree=[_tree_node("LICENSE", 200)],
        )
        without_license = _repo(license=None, tree=[])

        r1 = run_scoring(with_license)
        r2 = run_scoring(without_license)

        lic1 = _get_cat_score(r1, "Licensing")
        lic2 = _get_cat_score(r2, "Licensing")
        assert lic1 is not None
        assert lic2 is not None
        assert lic1.score > lic2.score

    def test_ci_present_increases_ci_score(self) -> None:
        with_ci = _repo(
            workflows=[
                _workflow("ci.yml"),
                _workflow("test.yml", "Tests"),
                _workflow("lint.yml", "Lint"),
                _workflow("deploy.yml", "Deploy"),
            ]
        )
        without_ci = _repo(workflows=[])

        r1 = run_scoring(with_ci)
        r2 = run_scoring(without_ci)

        ci1 = _get_cat_score(r1, "CI/CD")
        ci2 = _get_cat_score(r2, "CI/CD")
        assert ci1 is not None
        assert ci2 is not None
        assert ci1.score > ci2.score

    def test_security_features_improve_security_score(self) -> None:
        with_security = _repo(
            has_gitignore=True,
            tree=[
                _tree_node("SECURITY.md"),
                _tree_node(".github/dependabot.yml"),
                _tree_node(".github/secret-scanning.yml"),
            ],
            workflows=[_workflow("codeql-analysis.yml", "CodeQL")],
        )
        without_security = _repo(has_gitignore=False, workflows=[])

        r1 = run_scoring(with_security)
        r2 = run_scoring(without_security)

        sec1 = _get_cat_score(r1, "Security")
        sec2 = _get_cat_score(r2, "Security")
        assert sec1 is not None
        assert sec2 is not None
        assert sec1.score > sec2.score

    def test_all_findings_have_points(self) -> None:
        result = _repo()
        scoring = run_scoring(result)
        for cat in scoring.categories:
            for finding in cat.details:
                assert "points" in finding, f"{finding['rule']} missing 'points'"
                assert "max_points" in finding, f"{finding['rule']} missing 'max_points'"
                assert isinstance(finding["points"], int)
                assert isinstance(finding["max_points"], int)
                assert finding["points"] <= finding["max_points"]

    def test_pass_gives_full_weight(self) -> None:
        result = _repo(
            tree=[_tree_node("LICENSE", 200)],
            license=LicenseInfo(spdx_id="MIT", name="MIT License"),
        )
        scoring = run_scoring(result)
        for cat in scoring.categories:
            for finding in cat.details:
                if finding["status"] == "PASS":
                    assert finding["points"] == finding["max_points"], (
                        f"{finding['rule']} passed but points({finding['points']}) != max_points({finding['max_points']})"
                    )

    def test_fail_gives_zero_points(self) -> None:
        result = _repo(readme=None, tree=[], workflows=[], license=None, has_gitignore=False)
        scoring = run_scoring(result)
        for cat in scoring.categories:
            for finding in cat.details:
                if finding["status"] == "FAIL":
                    assert finding["points"] == 0, f"{finding['rule']} failed but points={finding['points']}"

    def test_grade_boundaries(self) -> None:
        from app.scoring.pipeline import calculate_grade

        assert calculate_grade(95) == "A"
        assert calculate_grade(85) == "B"
        assert calculate_grade(75) == "C"
        assert calculate_grade(65) == "D"
        assert calculate_grade(50) == "F"

    def test_docs_directory_improves_documentation_score(self) -> None:
        """A repo with docs/ should score higher in documentation."""
        with_docs = _repo(tree=[_tree_node("README.md", 500), _dir("docs"), _tree_node("docs/index.md")])
        without_docs = _repo(tree=[_tree_node("README.md", 500)])

        r1 = run_scoring(with_docs)
        r2 = run_scoring(without_docs)

        doc1 = _get_cat_score(r1, "Documentation")
        doc2 = _get_cat_score(r2, "Documentation")
        assert doc1 is not None
        assert doc2 is not None
        assert doc1.score >= doc2.score

    def test_renovate_improves_security_score(self) -> None:
        """A repo with Renovate should score higher in security than one with nothing."""
        with_renovate = _repo(tree=[_tree_node("renovate.json")])
        without_any = _repo()

        r1 = run_scoring(with_renovate)
        r2 = run_scoring(without_any)

        sec1 = _get_cat_score(r1, "Security")
        sec2 = _get_cat_score(r2, "Security")
        assert sec1 is not None
        assert sec2 is not None
        assert sec1.score > sec2.score

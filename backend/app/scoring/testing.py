from __future__ import annotations

from typing import TYPE_CHECKING

from app.scoring.rule import Category, Rule, RuleResult

if TYPE_CHECKING:
    from app.github.schemas import GitHubRepositoryData

TEST_DIR_PATTERNS = ["tests", "test", "spec", "__tests__", "test_"]
TEST_FILE_PATTERNS = ["_test.", ".test.", "_spec.", ".spec.", "test_"]

FRAMEWORK_INDICATORS: dict[str, list[str]] = {
    "pytest": ["conftest.py", "pytest.ini", "setup.cfg", "tox.ini", "noxfile.py"],
    "jest": ["jest.config.js", "jest.config.ts", "jest.config.json", "jest.config.mjs", "jest.config.cjs"],
    "vitest": ["vitest.config.ts", "vitest.config.js", "vitest.config.mts", "vitest.config.mjs"],
    "mocha": [".mocharc.yml", ".mocharc.js", ".mocharc.json", ".mocharc.cjs"],
    "jasmine": ["jasmine.json", "spec/support/jasmine.json"],
    "karma": ["karma.conf.js", "karma.conf.ts"],
    "cypress": ["cypress.config.ts", "cypress.config.js"],
    "playwright": ["playwright.config.ts", "playwright.config.js", "playwright.config.mjs"],
    "go_test": ["go.sum", "go.mod"],
    "cargo_test": ["Cargo.toml"],
    "gradle_test": ["build.gradle", "build.gradle.kts"],
    "maven_test": ["pom.xml"],
    "dotnet_test": ["*.csproj", "*.sln"],
    "rspec": ["Gemfile"],
    "phpunit": ["phpunit.xml", "phpunit.xml.dist"],
    "minitest": ["Gemfile"],
}

GO_TEST_EXTENSIONS = ("_test.go",)

COVERAGE_CONFIG_PATTERNS = [
    ".coveragerc",
    ".coveragerc.toml",
    "coverage.xml",
    "coverage.json",
    "jest.config.js",
    "jest.config.ts",
    "jest.config.mjs",
    "jest.config.cjs",
    "vitest.config.ts",
    "vitest.config.js",
    "vitest.config.mjs",
    "nyc.config.js",
    ".nycrc",
    ".nycrc.json",
    "codecov.yml",
    ".codecov.yml",
    "tox.ini",
]


class TestDirectoryRule(Rule):
    rule_id = "TEST_DIRECTORY"
    category = Category.TESTING
    weight = 5
    description = "Test directory or test files exist"

    def evaluate(self, data: GitHubRepositoryData) -> RuleResult:
        file_paths = [item.path for item in data.tree]

        for path in file_paths:
            parts = path.lower().split("/")
            for pattern in TEST_DIR_PATTERNS:
                if pattern in parts:
                    return self._pass(f"Test directory found: {path.rsplit('/', 1)[0]}/")

        for path in file_paths:
            for pattern in TEST_FILE_PATTERNS:
                if pattern in path.lower():
                    return self._pass(f"Test file found: {path}")

        return self._fail(
            "No test directories or test files found",
            "Add a tests/ directory with unit tests for your code",
        )


class TestFrameworkRule(Rule):
    rule_id = "TEST_FRAMEWORK"
    category = Category.TESTING
    weight = 5
    description = "Test framework detected"

    def evaluate(self, data: GitHubRepositoryData) -> RuleResult:
        file_paths = {item.path for item in data.tree}

        for framework, indicators in FRAMEWORK_INDICATORS.items():
            for indicator in indicators:
                if indicator in file_paths:
                    if framework == "go_test":
                        for p in file_paths:
                            if p.endswith(GO_TEST_EXTENSIONS[0]):
                                return self._pass(f"Test framework detected: Go test ({p})")
                    elif framework == "cargo_test":
                        if any("_test.go" not in p and p.endswith(".rs") for p in file_paths):
                            return self._pass("Test framework detected: Rust/Cargo (Cargo.toml present)")
                    elif framework == "gradle_test":
                        return self._pass("Test framework detected: Gradle (build.gradle present)")
                    elif framework == "maven_test":
                        return self._pass("Test framework detected: Maven (pom.xml present)")
                    elif framework == "dotnet_test":
                        for p in file_paths:
                            if p.endswith((".csproj", ".sln")):
                                return self._pass(f"Test framework detected: .NET ({p})")
                    elif framework == "phpunit":
                        return self._pass("Test framework detected: PHPUnit (phpunit.xml present)")
                    elif framework == "rspec":
                        for p in file_paths:
                            if p.endswith(("_test.rb", "_spec.rb")) or "spec/" in p:
                                return self._pass("Test framework detected: Ruby RSpec/Minitest")
                    else:
                        return self._pass(f"Test framework detected: {framework}")

        for path in file_paths:
            parts = path.lower().split("/")
            if "__tests__" in parts:
                return self._pass("Test framework detected: Jest (__tests__/ directory found)")

        has_test_files = False
        has_py_test_files = False
        for path in file_paths:
            if path.endswith(GO_TEST_EXTENSIONS[0]):
                return self._pass(f"Test framework detected: Go test ({path})")
            parts = path.lower().split("/")
            for pattern in TEST_DIR_PATTERNS:
                if pattern in parts:
                    has_test_files = True
                    break
            if not has_test_files:
                for pattern in TEST_FILE_PATTERNS:
                    if pattern in path.lower():
                        has_test_files = True
                        break
            basename = path.rsplit("/", 1)[-1]
            if (basename.startswith("test_") and basename.endswith(".py")) or (basename.endswith("_test.py")):
                has_py_test_files = True

        if has_test_files and "pyproject.toml" in file_paths:
            return self._pass("Test framework detected: pytest (pyproject.toml with test files)")

        if has_py_test_files:
            return self._pass("Test framework detected: Python unittest (test files found)")

        return self._fail(
            "No test framework detected",
            "Add pytest, jest, vitest, or another test framework",
        )


class CoverageConfigRule(Rule):
    rule_id = "COVERAGE_CONFIG"
    category = Category.TESTING
    weight = 5
    description = "Test coverage configuration exists"

    def evaluate(self, data: GitHubRepositoryData) -> RuleResult:
        file_paths = {item.path for item in data.tree}

        for pattern in COVERAGE_CONFIG_PATTERNS:
            if pattern in file_paths:
                return self._pass(f"Coverage configuration found: {pattern}")

        for path in file_paths:
            for pattern in COVERAGE_CONFIG_PATTERNS:
                if pattern in path.lower():
                    return self._pass(f"Coverage configuration found: {path}")

        return self._fail(
            "No test coverage configuration found",
            "Add coverage configuration (.coveragerc, jest.config.js, codecov.yml, etc.)",
        )


class CITestWorkflowRule(Rule):
    rule_id = "CI_TEST_WORKFLOW"
    category = Category.TESTING
    weight = 5
    description = "CI workflow includes test step"

    def evaluate(self, data: GitHubRepositoryData) -> RuleResult:
        if not data.workflows:
            return self._fail(
                "No CI workflows found",
                "Add a GitHub Actions workflow that runs tests",
            )

        test_keywords = [
            "test",
            "pytest",
            "jest",
            "vitest",
            "spec",
            "mocha",
            "cargo test",
            "go test",
            "unit",
            "integration",
            "e2e",
            "smoke",
            "regression",
            "coverage",
            "check",
        ]
        for workflow in data.workflows:
            name = (workflow.name or "").lower()
            path = (workflow.path or "").lower()
            combined = f"{name} {path}"
            if any(kw in combined for kw in test_keywords):
                return self._pass(f"CI test workflow found: {workflow.path}")

        return self._fail(
            "CI workflows exist but none appear to run tests",
            "Add a test step to your CI workflow (e.g., pytest, npm test, cargo test)",
        )


TESTING_RULES: list[Rule] = [
    TestDirectoryRule(),
    TestFrameworkRule(),
    CoverageConfigRule(),
    CITestWorkflowRule(),
]

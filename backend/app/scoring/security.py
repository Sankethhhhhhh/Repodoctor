from __future__ import annotations

import re

from app.github.schemas import GitHubRepositoryData
from app.scoring.rule import Category, Rule, RuleResult

SECRET_FILE_PATTERNS = [
    r"\.env$",
    r"\.env\.",
    r"credentials\.json",
    r"\.pem$",
    r"\.key$",
    r"id_rsa",
    r"secret",
]

COMMON_GITIGNORE_ITEMS = [
    "node_modules",
    "__pycache__",
    ".env",
    ".DS_Store",
    ".idea",
    ".vscode",
    "*.pyc",
    "*.pem",
    "*.key",
    "dist",
    "build",
    ".next",
    "target",
]

CODEQL_WORKFLOW_PATTERNS = [
    "codeql-analysis.yml",
    "codeql-analysis.yaml",
    "codeql.yml",
    "codeql.yaml",
]

SECRET_SCANNING_FILES = [
    ".github/secret-scanning.yml",
    ".github/secret-scanning.yaml",
    ".github/secret-scanning-pattern.yml",
    ".github/secret-scanning-pattern.yaml",
]

SECURITY_FILES = [
    "SECURITY.md",
    "SECURITY.txt",
    "SECURITY.rst",
    "SECURITY",
    "security.md",
    "SECURITY_CONTACTS",
    ".github/SECURITY.md",
    ".github/SECURITY.txt",
    ".github/SECURITY.rst",
]


class GitignoreRule(Rule):
    rule_id = "GITIGNORE_EXISTS"
    category = Category.SECURITY
    weight = 5
    description = ".gitignore file exists"

    @property
    def severity(self) -> str:
        return "high"

    @property
    def documentation(self) -> str | None:
        return "https://docs.github.com/en/get-started/getting-started-with-git/ignoring-files"

    def evaluate(self, data: GitHubRepositoryData) -> RuleResult:
        if data.has_gitignore:
            return self._pass(".gitignore found in repository root")
        return self._fail(
            "No .gitignore found",
            "Add a .gitignore to exclude build artifacts, dependencies, and secrets",
        )


class GitignoreCoverageRule(Rule):
    rule_id = "GITIGNORE_COVERAGE"
    category = Category.SECURITY
    weight = 5
    description = ".gitignore covers common patterns"

    @property
    def severity(self) -> str:
        return "medium"

    def evaluate(self, data: GitHubRepositoryData) -> RuleResult:
        if not data.has_gitignore:
            return self._fail(
                "Cannot evaluate .gitignore coverage: no .gitignore found",
                "Add a .gitignore with standard exclusions",
            )

        test_dir_parts = {
            "tests", "test", "spec", "__tests__", "test_apps", "test_fixtures",
            "fixtures", "examples", "example", "demo", "demos",
            "testdata", "test_data", "vendor", "third_party",
        }
        tree_paths = {item.path for item in data.tree}
        tree_basenames = {item.path.rsplit("/", 1)[-1] for item in data.tree}
        tree_dir_parts: set[str] = set()
        for p in tree_paths:
            parts = p.split("/")
            for part in parts[:-1]:
                tree_dir_parts.add(part)

        found_in_tree: list[str] = []
        for pattern in COMMON_GITIGNORE_ITEMS:
            if "*" in pattern:
                ext = pattern.replace("*", "")
                for p in tree_paths:
                    if p.endswith(ext):
                        path_parts = set(p.lower().split("/"))
                        if not (path_parts & test_dir_parts):
                            found_in_tree.append(pattern)
                            break
            else:
                matched = False
                if pattern in tree_basenames or pattern in tree_dir_parts:
                    matched = True
                if matched:
                    found_in_tree.append(pattern)

        if not found_in_tree:
            return self._pass("No common ignored items found in tracked files — .gitignore appears effective")
        if len(found_in_tree) == 1:
            return self._pass(
                f".gitignore mostly effective, but {found_in_tree[0]} found in tracked files"
            )
        return self._fail(
            f"Common ignored items found in tracked files: {', '.join(found_in_tree[:5])}",
            f"Add these to .gitignore: {', '.join(found_in_tree[:5])}",
        )


class SecretPatternsRule(Rule):
    rule_id = "SECRET_PATTERNS"
    category = Category.SECURITY
    weight = 5
    description = "No obvious secret files in the file tree"

    @property
    def severity(self) -> str:
        return "high"

    def evaluate(self, data: GitHubRepositoryData) -> RuleResult:
        test_dir_parts = {
            "tests", "test", "spec", "__tests__", "test_apps", "test_fixtures",
            "fixtures", "examples", "example", "demo", "demos",
            "testdata", "test_data", "test_data", "testdata",
        }
        docs_lib_parts = {
            "doc", "docs", "documentation", "lib", "libs", "library",
            "vendor", "node_modules", "third_party", "external",
        }
        secrets_found: list[str] = []
        for item in data.tree:
            parts = set(item.path.lower().split("/"))
            if parts & test_dir_parts:
                continue
            if parts & docs_lib_parts:
                continue
            filename = item.path.split("/")[-1]
            for pattern in SECRET_FILE_PATTERNS:
                if re.search(pattern, filename, re.IGNORECASE):
                    secrets_found.append(item.path)
                    break

        if not secrets_found:
            return self._pass("No obvious secret files detected in file tree")
        return self._fail(
            f"Potential secret files found: {', '.join(secrets_found[:3])}",
            "Remove secret files and add them to .gitignore",
        )


class DependabotRule(Rule):
    rule_id = "DEPENDABOT"
    category = Category.SECURITY
    weight = 5
    description = "Dependabot or Renovate configuration exists"

    @property
    def severity(self) -> str:
        return "medium"

    @property
    def documentation(self) -> str | None:
        return "https://docs.github.com/en/code-security/dependabot/dependabot-version-updates/configuration-options-for-the-dependabot.yml-file"

    def evaluate(self, data: GitHubRepositoryData) -> RuleResult:
        file_paths = {item.path for item in data.tree}
        dependabot_paths = [
            ".github/dependabot.yml",
            ".github/dependabot.yaml",
        ]
        for dp in dependabot_paths:
            hit = self._file_exists(file_paths, dp)
            if hit:
                return self._pass(f"Dependabot config found: {hit}")

        renovate_paths = [
            "renovate.json",
            "renovate.json5",
            ".renovaterc",
            ".renovaterc.json",
            ".github/renovate.json",
            ".github/renovate.json5",
        ]
        for rp in renovate_paths:
            hit = self._file_exists(file_paths, rp)
            if hit:
                return self._pass(f"Renovate config found: {hit}")

        return self._fail(
            "No Dependabot or Renovate configuration found",
            "Add .github/dependabot.yml for automated dependency updates",
        )


class SecurityPolicyRule(Rule):
    rule_id = "SECURITY_POLICY"
    category = Category.SECURITY
    weight = 5
    description = "Security policy exists"

    @property
    def severity(self) -> str:
        return "medium"

    @property
    def documentation(self) -> str | None:
        return "https://docs.github.com/en/code-security/security-advisories"

    def evaluate(self, data: GitHubRepositoryData) -> RuleResult:
        file_paths = {item.path for item in data.tree}
        hit = self._file_matches(file_paths, SECURITY_FILES)
        if hit:
            return self._pass(f"Security policy found: {hit}")
        return self._fail(
            "No SECURITY.md or security policy found",
            "Add a SECURITY.md with vulnerability reporting instructions",
        )


class CodeqlWorkflowRule(Rule):
    rule_id = "CODEQL_WORKFLOW"
    category = Category.SECURITY
    weight = 5
    description = "CodeQL analysis workflow exists"

    @property
    def severity(self) -> str:
        return "medium"

    @property
    def documentation(self) -> str | None:
        return "https://docs.github.com/en/code-security/code-scanning/automatically-scanning-your-code-for-vulnerabilities-and-errors/about-code-scanning"

    def evaluate(self, data: GitHubRepositoryData) -> RuleResult:
        for workflow in data.workflows:
            name = (workflow.name or "").lower()
            path = (workflow.path or "").lower()
            combined = f"{name} {path}"
            if "codeql" in combined:
                return self._pass(f"CodeQL workflow found: {workflow.path}")

        file_paths = {item.path for item in data.tree}
        for pattern in CODEQL_WORKFLOW_PATTERNS:
            if pattern in file_paths or f".github/workflows/{pattern}" in file_paths:
                return self._pass(f"CodeQL config found: {pattern}")

        return self._fail(
            "No CodeQL analysis workflow found",
            "Add a CodeQL workflow at .github/workflows/codeql-analysis.yml for security scanning",
        )


class SecretScanningRule(Rule):
    rule_id = "SECRET_SCANNING"
    category = Category.SECURITY
    weight = 5
    description = "Secret scanning configuration exists"

    @property
    def severity(self) -> str:
        return "medium"

    @property
    def documentation(self) -> str | None:
        return "https://docs.github.com/en/code-security/secret-scanning"

    def evaluate(self, data: GitHubRepositoryData) -> RuleResult:
        file_paths = {item.path for item in data.tree}
        for sf in SECRET_SCANNING_FILES:
            if self._file_exists(file_paths, sf):
                return self._pass(f"Secret scanning config found: {sf}")
        return self._fail(
            "No secret scanning configuration found",
            "Enable GitHub secret scanning or add .github/secret-scanning.yml",
        )


SECURITY_RULES: list[Rule] = [
    GitignoreRule(),
    GitignoreCoverageRule(),
    SecretPatternsRule(),
    DependabotRule(),
    SecurityPolicyRule(),
    CodeqlWorkflowRule(),
    SecretScanningRule(),
]

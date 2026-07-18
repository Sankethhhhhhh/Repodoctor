from __future__ import annotations

from app.github.schemas import GitHubRepositoryData
from app.scoring.rule import Category, Rule, RuleResult


class GitHubActionsRule(Rule):
    rule_id = "GITHUB_ACTIONS"
    category = Category.CI_CD
    weight = 5
    description = "GitHub Actions workflows exist"

    def evaluate(self, data: GitHubRepositoryData) -> RuleResult:
        if data.workflows:
            active = [w for w in data.workflows if w.state == "active"]
            return self._pass(f"Found {len(data.workflows)} GitHub Actions workflow(s) ({len(active)} active)")
        return self._fail(
            "No GitHub Actions workflows found",
            "Set up GitHub Actions for CI/CD automation",
        )


class BuildWorkflowRule(Rule):
    rule_id = "BUILD_WORKFLOW"
    category = Category.CI_CD
    weight = 5
    description = "Build or CI workflow exists"

    def evaluate(self, data: GitHubRepositoryData) -> RuleResult:
        build_keywords = [
            "build", "compile", "make", "ci", "continuous-integration",
            "check", "validate", "verify", "pr", "merge", "quality",
            "release", "deploy", "test", "lint", "workflow",
        ]
        for workflow in data.workflows:
            name = (workflow.name or "").lower()
            path = (workflow.path or "").lower()
            combined = f"{name} {path}"
            if any(kw in combined for kw in build_keywords):
                return self._pass(f"Build/CI workflow found: {workflow.path}")
        if data.workflows:
            return self._pass(
                f"GitHub Actions configured ({len(data.workflows)} workflows present)"
            )
        return self._fail(
            "No build or CI workflow found",
            "Add a CI workflow that builds and validates your project",
        )


class LintWorkflowRule(Rule):
    rule_id = "LINT_WORKFLOW"
    category = Category.CI_CD
    weight = 5
    description = "Lint or code quality workflow exists"

    def evaluate(self, data: GitHubRepositoryData) -> RuleResult:
        lint_keywords = [
            "lint", "format", "check", "style", "quality",
            "flake8", "ruff", "eslint", "prettier", "clippy",
            "deny", "audit", "swiftlint", "rubocop", "mypy",
            "pyright", "tsc", "biome", "oxlint", "typecheck", "type-check",
            "validate", "verify",
        ]
        for workflow in data.workflows:
            name = (workflow.name or "").lower()
            path = (workflow.path or "").lower()
            combined = f"{name} {path}"
            if any(kw in combined for kw in lint_keywords):
                return self._pass(f"Lint/quality workflow found: {workflow.path}")
        return self._fail(
            "No lint or code quality workflow found",
            "Add a CI workflow for linting and code quality checks",
        )


class DeployWorkflowRule(Rule):
    rule_id = "DEPLOY_WORKFLOW"
    category = Category.CI_CD
    weight = 5
    description = "Deploy or release workflow exists"

    def evaluate(self, data: GitHubRepositoryData) -> RuleResult:
        deploy_keywords = [
            "deploy", "release", "publish", "ship", "cdn",
            "pages", "vercel", "netlify", "nightly", "canary",
            "tag", "draft", "pre-release",
        ]
        for workflow in data.workflows:
            name = (workflow.name or "").lower()
            path = (workflow.path or "").lower()
            combined = f"{name} {path}"
            if any(kw in combined for kw in deploy_keywords):
                return self._pass(f"Deploy/release workflow found: {workflow.path}")
        return self._fail(
            "No deploy or release workflow found",
            "Add a CI/CD workflow for automated deployments or releases",
        )


CI_CD_RULES: list[Rule] = [
    GitHubActionsRule(),
    BuildWorkflowRule(),
    LintWorkflowRule(),
    DeployWorkflowRule(),
]

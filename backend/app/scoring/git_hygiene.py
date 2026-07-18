from __future__ import annotations

import re
from typing import TYPE_CHECKING

from app.scoring.rule import Category, Rule, RuleResult

if TYPE_CHECKING:
    from app.github.schemas import GitHubRepositoryData

LOW_EFFORT_PATTERNS = [
    r"^update$",
    r"^fix$",
    r"^wip$",
    r"^asdf$",
    r"^qwer$",
    r"^test$",
    r"^tmp$",
    r"^temp$",
    r"^a+$",
    r"^\.+$",
]

CODEOWNERS_FILES = [
    "CODEOWNERS",
    ".github/CODEOWNERS",
    "docs/CODEOWNERS",
    "OWNERS",
]

PR_TEMPLATE_FILES = [
    ".github/pull_request_template.md",
    ".github/PULL_REQUEST_TEMPLATE.md",
    "PULL_REQUEST_TEMPLATE.md",
    "pull_request_template.md",
]

ISSUE_TEMPLATE_FILES = [
    ".github/ISSUE_TEMPLATE.md",
    ".github/ISSUE_TEMPLATE/",
    "ISSUE_TEMPLATE.md",
]


class MeaningfulCommitsRule(Rule):
    rule_id = "MEANINGFUL_COMMITS"
    category = Category.GIT_HYGIENE
    weight = 5
    description = "Commit messages are meaningful"

    def evaluate(self, data: GitHubRepositoryData) -> RuleResult:
        if not data.commits:
            return self._fail(
                "No commit history available",
                "Ensure commits have meaningful messages",
            )

        low_effort = 0
        for commit in data.commits:
            first_line = commit.message.split("\n")[0].strip()
            if len(first_line) < 5:
                low_effort += 1
                continue
            for pattern in LOW_EFFORT_PATTERNS:
                if re.match(pattern, first_line, re.IGNORECASE):
                    low_effort += 1
                    break

        total = len(data.commits)
        ratio = low_effort / total if total > 0 else 0

        if ratio <= 0.2:
            return self._pass(f"{total - low_effort}/{total} commits have meaningful messages")
        return self._fail(
            f"{low_effort}/{total} commits have low-effort messages",
            "Write descriptive commit messages explaining what changed and why",
        )


class CommitFrequencyRule(Rule):
    rule_id = "COMMIT_FREQUENCY"
    category = Category.GIT_HYGIENE
    weight = 5
    description = "Repository has sufficient commit history"

    def evaluate(self, data: GitHubRepositoryData) -> RuleResult:
        if not data.commits:
            return self._fail(
                "No commit history available",
                "Maintain a regular commit history",
            )

        total = len(data.commits)
        if total >= 10:
            return self._pass(f"{total} commits found in history")
        if total >= 3:
            return self._pass(f"{total} commits found (minimal but present)")
        return self._fail(
            f"Only {total} commit(s) found — possible single-commit dump",
            "Make incremental commits with descriptive messages",
        )


class ContributorActivityRule(Rule):
    rule_id = "CONTRIBUTOR_ACTIVITY"
    category = Category.GIT_HYGIENE
    weight = 5
    description = "Multiple contributors or consistent activity"

    def evaluate(self, data: GitHubRepositoryData) -> RuleResult:
        if not data.commits:
            return self._fail(
                "No commit history available",
                "Encourage contributions from multiple developers",
            )

        authors = {c.author_name for c in data.commits if c.author_name}

        if len(authors) >= 2:
            return self._pass(f"{len(authors)} unique contributors found")
        if len(authors) == 1 and len(data.commits) >= 5:
            return self._pass("Single contributor with active commit history")
        return self._fail(
            f"Only {len(authors)} contributor(s) with {len(data.commits)} commit(s)",
            "Encourage contributions from other developers",
        )


class CodeownersExistsRule(Rule):
    rule_id = "CODEOWNERS_EXISTS"
    category = Category.GIT_HYGIENE
    weight = 5
    description = "CODEOWNERS or OWNERS file exists"

    def evaluate(self, data: GitHubRepositoryData) -> RuleResult:
        file_paths = {item.path for item in data.tree}
        hit = self._file_matches(file_paths, CODEOWNERS_FILES)
        if hit:
            return self._pass(f"Code ownership file found: {hit}")
        return self._fail(
            "No CODEOWNERS or OWNERS file found",
            "Add a CODEOWNERS file to define code review ownership",
        )


class PrTemplateExistsRule(Rule):
    rule_id = "PR_TEMPLATE_EXISTS"
    category = Category.GIT_HYGIENE
    weight = 5
    description = "Pull request template exists"

    def evaluate(self, data: GitHubRepositoryData) -> RuleResult:
        file_paths = {item.path for item in data.tree}
        hit = self._file_matches(file_paths, PR_TEMPLATE_FILES)
        if hit:
            return self._pass(f"PR template found: {hit}")
        return self._fail(
            "No pull request template found",
            "Add a PR template at .github/pull_request_template.md",
        )


class IssueTemplateExistsRule(Rule):
    rule_id = "ISSUE_TEMPLATE_EXISTS"
    category = Category.GIT_HYGIENE
    weight = 5
    description = "Issue template exists"

    def evaluate(self, data: GitHubRepositoryData) -> RuleResult:
        file_paths = {item.path for item in data.tree}
        tree_dirs = {item.path for item in data.tree if item.type == "tree"}

        for it in ISSUE_TEMPLATE_FILES:
            if it.endswith("/"):
                if self._dir_exists(tree_dirs, it):
                    return self._pass(f"Issue template directory found: {it}")
            elif self._file_exists(file_paths, it):
                return self._pass(f"Issue template found: {it}")

        hit = self._has_file_under(file_paths, ".github/ISSUE_TEMPLATE")
        if hit:
            return self._pass(f"Issue template found: {hit}")

        return self._fail(
            "No issue template found",
            "Add issue templates at .github/ISSUE_TEMPLATE/ or .github/ISSUE_TEMPLATE.md",
        )


class ReleasesExistRule(Rule):
    rule_id = "RELEASES_EXIST"
    category = Category.GIT_HYGIENE
    weight = 5
    description = "Repository has releases"

    def evaluate(self, data: GitHubRepositoryData) -> RuleResult:
        if data.releases:
            latest = data.releases[0].tag_name
            return self._pass(f"{len(data.releases)} release(s) found (latest: {latest})")
        return self._fail(
            "No releases found",
            "Create releases to mark stable versions of your project",
        )


GIT_HYGIENE_RULES: list[Rule] = [
    MeaningfulCommitsRule(),
    CommitFrequencyRule(),
    ContributorActivityRule(),
    CodeownersExistsRule(),
    PrTemplateExistsRule(),
    IssueTemplateExistsRule(),
    ReleasesExistRule(),
]

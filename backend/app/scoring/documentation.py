from __future__ import annotations

from app.github.schemas import GitHubRepositoryData
from app.scoring.rule import Category, Rule, RuleResult

README_MIN_LENGTH = 200
README_SECTION_KEYWORDS = {
    "installation": ["install", "installation", "setup", "getting started"],
    "usage": ["usage", "example", "examples", "quick start", "how to"],
    "license": ["license", "licensing"],
}

CONTRIBUTING_FILES = [
    "CONTRIBUTING.md",
    "CONTRIBUTING",
    "CONTRIBUTING.rst",
    "CONTRIBUTING.txt",
    ".github/CONTRIBUTING.md",
    ".github/CONTRIBUTING.rst",
    ".github/CONTRIBUTING.txt",
]

CODE_OF_CONDUCT_FILES = [
    "CODE_OF_CONDUCT.md",
    "CODE_OF_CONDUCT",
    "CODE_OF_CONDUCT.rst",
    "CODE_OF_CONDUCT.txt",
    ".github/CODE_OF_CONDUCT.md",
    "code-of-conduct.md",
]

CHANGELOG_FILES = [
    "CHANGELOG.md",
    "CHANGELOG",
    "CHANGELOG.rst",
    "CHANGELOG.txt",
    "CHANGES.md",
    "CHANGES",
    "CHANGES.rst",
    "HISTORY.md",
    "HISTORY",
]


class ReadmeExistsRule(Rule):
    rule_id = "README_EXISTS"
    category = Category.DOCUMENTATION
    weight = 5
    description = "README file exists in the repository root"

    def evaluate(self, data: GitHubRepositoryData) -> RuleResult:
        if data.readme and len(data.readme.strip()) > 0:
            return self._pass("README.md found in repository root")
        return self._fail(
            "No README.md found in repository",
            "Add a README.md with description, installation, and usage instructions",
        )


class ReadmeLengthRule(Rule):
    rule_id = "README_LENGTH"
    category = Category.DOCUMENTATION
    weight = 5
    description = "README has sufficient length"

    def evaluate(self, data: GitHubRepositoryData) -> RuleResult:
        if not data.readme:
            return self._fail(
                "Cannot evaluate README length: no README found",
                "Add a README.md with at least 200 characters of content",
            )
        length = len(data.readme.strip())
        if length >= README_MIN_LENGTH:
            return self._pass(f"README is {length} characters (minimum: {README_MIN_LENGTH})")
        return self._fail(
            f"README is only {length} characters (minimum: {README_MIN_LENGTH})",
            "Expand your README with installation, usage, and contribution guidelines",
        )


class ReadmeSectionRule(Rule):
    rule_id = "README_SECTIONS"
    category = Category.DOCUMENTATION
    weight = 5
    description = "README contains key sections"

    def evaluate(self, data: GitHubRepositoryData) -> RuleResult:
        if not data.readme:
            return self._fail(
                "Cannot evaluate README sections: no README found",
                "Add a README with Installation, Usage, and License sections",
            )

        readme_lower = data.readme.lower()
        found_sections: list[str] = []
        missing_sections: list[str] = []

        for section, keywords in README_SECTION_KEYWORDS.items():
            if any(kw in readme_lower for kw in keywords):
                found_sections.append(section)
            else:
                missing_sections.append(section)

        if len(found_sections) >= 2:
            return self._pass(f"README contains sections: {', '.join(found_sections)}")
        return self._fail(
            f"README missing sections: {', '.join(missing_sections)}",
            f"Add at least 2 of these sections: {', '.join(README_SECTION_KEYWORDS.keys())}",
        )


class ContributingExistsRule(Rule):
    rule_id = "CONTRIBUTING_EXISTS"
    category = Category.DOCUMENTATION
    weight = 5
    description = "CONTRIBUTING file exists"

    def evaluate(self, data: GitHubRepositoryData) -> RuleResult:
        file_paths = {item.path for item in data.tree}
        hit = self._file_matches(file_paths, CONTRIBUTING_FILES)
        if hit:
            return self._pass(f"Contributing guide found: {hit}")
        return self._fail(
            "No CONTRIBUTING file found",
            "Add a CONTRIBUTING.md with guidelines for contributors",
        )


class CodeOfConductRule(Rule):
    rule_id = "CODE_OF_CONDUCT"
    category = Category.DOCUMENTATION
    weight = 5
    description = "Code of Conduct file exists"

    def evaluate(self, data: GitHubRepositoryData) -> RuleResult:
        file_paths = {item.path for item in data.tree}
        hit = self._file_matches(file_paths, CODE_OF_CONDUCT_FILES)
        if hit:
            return self._pass(f"Code of Conduct found: {hit}")
        return self._fail(
            "No CODE_OF_CONDUCT file found",
            "Add a CODE_OF_CONDUCT.md to establish community standards",
        )


class ChangelogExistsRule(Rule):
    rule_id = "CHANGELOG_EXISTS"
    category = Category.DOCUMENTATION
    weight = 5
    description = "Changelog file or releases exist"

    def evaluate(self, data: GitHubRepositoryData) -> RuleResult:
        file_paths = {item.path for item in data.tree}
        hit = self._file_matches(file_paths, CHANGELOG_FILES)
        if hit:
            return self._pass(f"Changelog found: {hit}")
        if data.releases and len(data.releases) >= 3:
            latest = data.releases[0].tag_name
            return self._pass(
                f"No CHANGELOG file, but {len(data.releases)} releases found (latest: {latest}) — releases serve as changelog"
            )
        return self._fail(
            "No CHANGELOG file or sufficient releases found",
            "Add a CHANGELOG.md or create releases to document version history",
        )


class DocsDirectoryRule(Rule):
    rule_id = "DOCS_DIRECTORY"
    category = Category.DOCUMENTATION
    weight = 3
    description = "Documentation directory exists"

    @property
    def severity(self) -> str:
        return "low"

    def evaluate(self, data: GitHubRepositoryData) -> RuleResult:
        tree_dirs = {item.path for item in data.tree if item.type == "tree"}
        for name in ["docs", "doc", "documentation", "website", "site"]:
            if self._dir_exists(tree_dirs, name):
                return self._pass(f"Documentation directory found: {name}/")
        return self._fail(
            "No documentation directory found",
            "Add a docs/ directory with detailed documentation",
        )


DOCUMENTATION_RULES: list[Rule] = [
    ReadmeExistsRule(),
    ReadmeLengthRule(),
    ReadmeSectionRule(),
    ContributingExistsRule(),
    CodeOfConductRule(),
    ChangelogExistsRule(),
    DocsDirectoryRule(),
]

from __future__ import annotations

from app.github.schemas import GitHubRepositoryData
from app.scoring.rule import Category, Rule, RuleResult

LICENSE_FILE_NAMES = [
    "LICENSE",
    "LICENSE.md",
    "LICENSE.txt",
    "LICENSE.rst",
    "LICENCE",
    "LICENCE.md",
    "LICENCE.txt",
    "COPYING",
    "COPYING.md",
    "COPYING.txt",
]


class LicenseFileRule(Rule):
    rule_id = "LICENSE_FILE"
    category = Category.LICENSING
    weight = 5
    description = "LICENSE file exists in the repository"

    def evaluate(self, data: GitHubRepositoryData) -> RuleResult:
        file_paths = {item.path for item in data.tree}
        hit = self._file_matches(file_paths, LICENSE_FILE_NAMES)
        if hit:
            return self._pass(f"License file found: {hit}")
        return self._fail(
            "No LICENSE file found",
            "Add a LICENSE file to clarify usage rights",
        )


class LicenseTypeRule(Rule):
    rule_id = "LICENSE_TYPE"
    category = Category.LICENSING
    weight = 5
    description = "License type is identified (SPDX)"

    def evaluate(self, data: GitHubRepositoryData) -> RuleResult:
        if data.license and data.license.spdx_id:
            return self._pass(f"License identified via SPDX: {data.license.spdx_id}")
        return self._fail(
            "No SPDX-identified license found",
            "Add an SPDX-recognized license (MIT, Apache-2.0, GPL-3.0, etc.)",
        )


LICENSING_RULES: list[Rule] = [
    LicenseFileRule(),
    LicenseTypeRule(),
]

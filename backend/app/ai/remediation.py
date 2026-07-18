from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from app.ai.provider import get_provider

if TYPE_CHECKING:
    from app.models.models import Report

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert software engineer helping developers improve their GitHub repositories.
For each failed rule, provide:
1. A clear explanation of what the issue is
2. Why it matters for repository quality
3. Step-by-step instructions to fix it
4. Example code or configuration where applicable

Be concise, practical, and actionable. Format your response as JSON with this structure:
{
  "remediations": [
    {
      "rule": "RULE_ID",
      "explanation": "...",
      "why_it_matters": "...",
      "steps": ["step1", "step2"],
      "example": "optional code/config example",
      "documentation_links": ["url1"]
    }
  ]
}"""

BUILD_PROMPT_TEMPLATE = """\
Analyze the following failed rules for the repository "{repo_name}" \
and provide remediation guidance.

Failed Rules:
{failed_rules}

Provide a JSON response with remediations for each failed rule."""


def _build_prompt(report: Report, failed_rules: list[dict[str, object]]) -> str:
    rule_lines = []
    for rule in failed_rules:
        parts = [
            f"- Rule: {rule.get('rule_id', rule.get('rule', 'unknown'))}",
            f"  Severity: {rule.get('severity', 'medium')}",
            f"  Evidence: {rule.get('evidence', 'N/A')}",
        ]
        if rule.get("recommendation"):
            parts.append(f"  Recommendation: {rule['recommendation']}")
        rule_lines.append("\n".join(parts))

    return BUILD_PROMPT_TEMPLATE.format(
        repo_name=report.repo_full_name,
        failed_rules="\n\n".join(rule_lines),
    )


async def generate_remediation(report: Report) -> dict[str, object]:
    rules_data: list[dict[str, object]] = json.loads(report.rules) if report.rules else []
    failed_rules = [r for r in rules_data if not r.get("passed", True)]

    if not failed_rules:
        return {"remediations": [], "message": "All rules passed!"}

    provider = get_provider()
    prompt = _build_prompt(report, failed_rules)

    try:
        response_text = await provider.generate(prompt, system=SYSTEM_PROMPT)
        result: dict[str, object] = json.loads(response_text)
        return result
    except json.JSONDecodeError:
        return {"remediations": [], "raw_response": response_text}
    except Exception:
        logger.exception("AI remediation failed")
        return {"remediations": [], "error": "Remediation generation failed"}

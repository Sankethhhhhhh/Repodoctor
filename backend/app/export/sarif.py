from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.models import Report

SARIF_VERSION = "2.1.0"
SARIF_SCHEMA = "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json"

SEVERITY_MAP = {
    "high": "error",
    "medium": "warning",
    "low": "note",
    "info": "note",
}

LEVEL_MAP = {
    "high": "error",
    "medium": "warning",
    "low": "note",
    "info": "none",
}


def generate_sarif(report: Report) -> str:
    rules = json.loads(report.rules) if report.rules else []
    recommendations = json.loads(report.recommendations) if report.recommendations else []

    rec_map: dict[str, str] = {}
    for rec in recommendations:
        if isinstance(rec, dict):
            rule_id = rec.get("rule", "")
            msg = rec.get("message", rec.get("recommendation", ""))
            if rule_id and msg:
                rec_map[rule_id] = msg

    tool_rules: list[dict[str, object]] = []
    seen_rules: set[str] = set()
    for rule in rules:
        rule_id = rule.get("id", "unknown")
        if rule_id in seen_rules:
            continue
        seen_rules.add(rule_id)
        tool_rule: dict[str, object] = {
            "id": rule_id,
            "shortDescription": {"text": rule.get("evidence", "")},
        }
        if rule.get("documentation"):
            tool_rule["helpUri"] = rule["documentation"]
        tool_rules.append(tool_rule)

    results: list[dict[str, object]] = []
    for rule in rules:
        rule_id = rule.get("id", "unknown")
        passed = rule.get("passed", False)
        evidence = rule.get("evidence", "")
        severity = rule.get("severity", "medium")
        recommendation = rule.get("recommendation", "") or rec_map.get(rule_id, "")

        sarif_level = LEVEL_MAP.get(severity, "warning")

        result: dict[str, object] = {
            "ruleId": rule_id,
            "level": sarif_level if not passed else "none",
            "message": {"text": evidence},
            "locations": [
                {
                    "physicalLocation": {
                        "artifactLocation": {
                            "uri": report.repo_full_name,
                            "uriBaseId": "%SRCROOT%",
                        },
                        "region": {"startLine": 1},
                    }
                }
            ],
        }

        if not passed and recommendation:
            result["fixes"] = [
                {
                    "description": {"text": recommendation},
                    "artifactChanges": [],
                }
            ]

        results.append(result)

    sarif: dict[str, object] = {
        "$schema": SARIF_SCHEMA,
        "version": SARIF_VERSION,
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "RepoDoctor",
                        "version": "0.1.0",
                        "informationUri": "https://github.com/repodoctor/repodoctor",
                        "rules": tool_rules,
                    }
                },
                "results": results,
                "columnKind": "utf16CodeUnits",
            }
        ],
    }

    return json.dumps(sarif, indent=2)

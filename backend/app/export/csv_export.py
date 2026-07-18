from __future__ import annotations

import csv
import io
import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.models import Report


def generate_csv(report: Report) -> str:
    categories = json.loads(report.category_breakdown) if report.category_breakdown else []
    rules = json.loads(report.rules) if report.rules else []

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["Repository Health Report"])
    writer.writerow(["Repository", report.repo_full_name])
    writer.writerow(["URL", report.repo_url])
    writer.writerow(["Score", str(report.score)])
    writer.writerow(["Grade", report.grade])
    writer.writerow(["Commit SHA", report.commit_sha])
    writer.writerow(["Generated", str(report.created_at)])
    writer.writerow([])

    writer.writerow(["Category", "Score", "Max Score", "Percentage"])
    for cat in categories:
        cat_score = cat.get("score", 0)
        cat_max = cat.get("max_score", 0)
        cat_pct = round(cat_score / cat_max * 100, 1) if cat_max > 0 else 0
        writer.writerow([cat.get("name", ""), str(cat_score), str(cat_max), f"{cat_pct}%"])
    writer.writerow([])

    writer.writerow(["Rule", "Category", "Status", "Severity", "Weight", "Evidence", "Recommendation"])
    for rule in rules:
        writer.writerow(
            [
                rule.get("id", ""),
                rule.get("category", ""),
                "PASS" if rule.get("passed", False) else "FAIL",
                rule.get("severity", "medium"),
                str(rule.get("weight", 0)),
                rule.get("evidence", ""),
                rule.get("recommendation", "") or "",
            ]
        )

    return output.getvalue()

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from markupsafe import escape

if TYPE_CHECKING:
    from app.models.models import Report


def generate_html(report: Report) -> str:
    categories = json.loads(report.category_breakdown) if report.category_breakdown else []
    rules = json.loads(report.rules) if report.rules else []
    recommendations = json.loads(report.recommendations) if report.recommendations else []

    total_rules = len(rules)
    passed_rules = sum(1 for r in rules if r.get("passed", False))
    failed_rules = total_rules - passed_rules

    repo_name = escape(report.repo_full_name)
    repo_url = escape(report.repo_url)
    commit_sha = escape(report.commit_sha)
    grade = escape(report.grade)
    created_at = escape(str(report.created_at))

    category_rows = ""
    for cat in categories:
        cat_name = escape(str(cat.get("name", "Unknown")))
        cat_score = cat.get("score", 0)
        cat_max = cat.get("max_score", 0)
        cat_pct = round(cat_score / cat_max * 100, 1) if cat_max > 0 else 0

        detail_rows = ""
        details = cat.get("details", [])
        for d in details:
            if isinstance(d, dict):
                rule_id = escape(str(d.get("rule", "unknown")))
                status = escape(str(d.get("status", "?")))
                severity = escape(str(d.get("severity", "medium")))
                evidence = escape(str(d.get("evidence", "")))
                status_class = "pass" if status == "PASS" else "fail"
                detail_rows += f"""
                <tr>
                    <td>{rule_id}</td>
                    <td class="{status_class}">{status}</td>
                    <td>{severity}</td>
                    <td>{evidence}</td>
                </tr>"""

        category_rows += f"""
        <div class="category">
            <h3>{cat_name} ({cat_pct}%)</h3>
            <p>Score: {cat_score}/{cat_max}</p>
            <table>
                <thead>
                    <tr><th>Rule</th><th>Status</th><th>Severity</th><th>Evidence</th></tr>
                </thead>
                <tbody>{detail_rows}
                </tbody>
            </table>
        </div>"""

    rec_items = ""
    for rec in recommendations:
        if isinstance(rec, dict):
            msg = escape(str(rec.get("message", rec.get("recommendation", ""))))
        else:
            msg = escape(str(rec))
        rec_items += f"<li>{msg}</li>"

    if not rec_items:
        rec_items = "<li>No recommendations. Great job!</li>"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RepoDoctor Report: {repo_name}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI',
            Roboto, sans-serif; background: #f8f9fa; color: #333;
            line-height: 1.6; padding: 2rem; }}
        .container {{ max-width: 900px; margin: 0 auto; background: white;
            border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            padding: 2rem; }}
        h1 {{ color: #1a1a1a; margin-bottom: 0.5rem; }}
        h2 {{ color: #2c3e50; margin: 1.5rem 0 0.75rem; border-bottom: 2px solid #eee; padding-bottom: 0.5rem; }}
        h3 {{ color: #34495e; margin: 1rem 0 0.5rem; }}
        .meta {{ color: #666; margin-bottom: 1.5rem; }}
        .meta a {{ color: #3498db; text-decoration: none; }}
        .meta a:hover {{ text-decoration: underline; }}
        .summary-grid {{ display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 1rem; margin: 1rem 0; }}
        .summary-card {{ background: #f8f9fa; border-radius: 6px; padding: 1rem; text-align: center; }}
        .summary-card .value {{ font-size: 1.5rem; font-weight: bold; color: #2c3e50; }}
        .summary-card .label {{ font-size: 0.85rem; color: #666; }}
        .grade {{ font-size: 2rem; font-weight: bold; }}
        .grade-a {{ color: #27ae60; }}
        .grade-b {{ color: #2ecc71; }}
        .grade-c {{ color: #f39c12; }}
        .grade-d {{ color: #e67e22; }}
        .grade-f {{ color: #e74c3c; }}
        table {{ width: 100%; border-collapse: collapse; margin: 0.5rem 0 1.5rem; }}
        th, td {{ padding: 0.5rem 0.75rem; text-align: left; border-bottom: 1px solid #eee; }}
        th {{ background: #f8f9fa; font-weight: 600; color: #555; }}
        .pass {{ color: #27ae60; font-weight: 600; }}
        .fail {{ color: #e74c3c; font-weight: 600; }}
        .category {{ margin-bottom: 1.5rem; }}
        ol {{ padding-left: 1.5rem; }}
        li {{ margin-bottom: 0.5rem; }}
        .footer {{ margin-top: 2rem; padding-top: 1rem;
            border-top: 1px solid #eee; color: #999;
            font-size: 0.85rem; text-align: center; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Repository Health Report</h1>
        <div class="meta">
            <p><strong>Repository:</strong> <a href="{repo_url}">{repo_name}</a></p>
            <p><strong>Commit:</strong> <code>{commit_sha}</code></p>
            <p><strong>Generated:</strong> {created_at}</p>
        </div>

        <h2>Summary</h2>
        <div class="summary-grid">
            <div class="summary-card">
                <div class="value">{report.score}%</div>
                <div class="label">Overall Score</div>
            </div>
            <div class="summary-card">
                <div class="value grade grade-{grade.lower()}">{grade}</div>
                <div class="label">Grade</div>
            </div>
            <div class="summary-card">
                <div class="value">{passed_rules}</div>
                <div class="label">Passed Rules</div>
            </div>
            <div class="summary-card">
                <div class="value">{failed_rules}</div>
                <div class="label">Failed Rules</div>
            </div>
            <div class="summary-card">
                <div class="value">{total_rules}</div>
                <div class="label">Total Rules</div>
            </div>
        </div>

        <h2>Category Breakdown</h2>
        {category_rows}

        <h2>Recommendations</h2>
        <ol>{rec_items}</ol>

        <div class="footer">
            <p>Generated by RepoDoctor v0.1.0</p>
        </div>
    </div>
</body>
</html>"""

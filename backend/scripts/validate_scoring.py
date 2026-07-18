"""Validate scoring engine against real GitHub repositories."""

import asyncio
import time

from app.config import settings
from app.github.client import GitHubClient
from app.github.service import GitHubService
from app.scoring.pipeline import run_scoring


REPOS = [
    "vercel/next.js",
    "microsoft/vscode",
    "facebook/react",
    "fastapi/fastapi",
    "python/cpython",
    "kubernetes/kubernetes",
]


async def validate() -> None:
    token = settings.github_token or None
    client = GitHubClient(token=token)
    service = GitHubService(client)

    try:
        for i, repo_url in enumerate(REPOS):
            if i > 0:
                delay = 3 if token else 12
                print(f"  (waiting {delay}s to avoid rate limits...)")
                time.sleep(delay)

            owner, repo = repo_url.split("/")
            print(f"\n{'='*70}")
            print(f"  {repo_url}")
            print(f"{'='*70}")

            try:
                data = await service.fetch_repository_data(owner, repo)
            except Exception as e:
                print(f"  ERROR: {type(e).__name__}: {e}")
                continue

            result = run_scoring(data)

            print(f"  Score:  {result.overall_score}/100  ({result.grade})")
            print(f"  Rules:  {len(result.rules)} evaluated")
            print()

            for cat in result.categories:
                passed = sum(1 for d in cat.details if d["status"] == "PASS")
                total = len(cat.details)
                pts = sum(d["points"] for d in cat.details)
                mx = sum(d["max_points"] for d in cat.details)
                print(f"  {cat.name:20s}  {pts:2d}/{mx:2d} pts  ({passed}/{total} rules passed)")
                for d in cat.details:
                    mark = "  + " if d["status"] == "PASS" else "  - "
                    pts_str = f"{d['points']}/{d['max_points']}"
                    print(f"    {mark}{d['rule']:30s} {pts_str:>7s}  {d['evidence'][:70]}")

            print()
            failed_rules = [r for r in result.rules if not r.passed]
            print(f"  Failed rules ({len(failed_rules)}):")
            for r in failed_rules:
                print(f"    - [{r.rule_id}] {r.evidence[:70]}")
                if r.recommendation:
                    print(f"      >> {r.recommendation}")
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(validate())

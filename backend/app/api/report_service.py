import logging

from app.cache.service import cache_service
from app.github.service import GitHubService, parse_repo_url
from app.repositories.report_repo import ReportRepository
from app.scoring.pipeline import ScoringResult, run_scoring

logger = logging.getLogger(__name__)

GITHUB_BASE_URL = "https://github.com"


def build_repo_url(owner: str, repo: str) -> str:
    return f"{GITHUB_BASE_URL}/{owner}/{repo}"


def compute_summary(result: ScoringResult) -> dict[str, int]:
    total_rules = len(result.rules)
    passed_rules = sum(1 for r in result.rules if r.passed)
    failed_rules = total_rules - passed_rules

    overall_percentage = result.overall_score

    categories_passed = 0
    categories_failed = 0
    for cat in result.categories:
        if cat.max_score > 0:
            ratio = cat.score / cat.max_score
            if ratio >= 0.5:
                categories_passed += 1
            else:
                categories_failed += 1

    return {
        "overall_percentage": overall_percentage,
        "grade": result.grade,
        "passed_rules": passed_rules,
        "failed_rules": failed_rules,
        "total_rules": total_rules,
        "categories_passed": categories_passed,
        "categories_failed": categories_failed,
    }


def deduplicate_recommendations(recommendations: list[str]) -> list[str]:
    return list(dict.fromkeys(recommendations))


class ReportService:
    def __init__(
        self,
        github_service: GitHubService,
        report_repo: ReportRepository,
    ) -> None:
        self.github = github_service
        self.report_repo = report_repo

    async def analyze(self, url: str) -> object:
        owner, repo = parse_repo_url(url)

        logger.info("Fetching repository data for %s/%s", owner, repo)
        repo_data = await self.github.fetch_repository_data(owner, repo)
        logger.info(
            "Fetched %d files, %d commits, %d workflows for %s/%s",
            len(repo_data.tree),
            len(repo_data.commits),
            len(repo_data.workflows),
            owner,
            repo,
        )

        logger.info("Running scoring engine for %s/%s", owner, repo)
        result = run_scoring(repo_data)
        result_dict = result.to_dict()
        logger.info("Scoring complete for %s/%s: score=%s grade=%s", owner, repo, result.overall_score, result.grade)

        category_breakdown = result_dict["categories"]
        rules_data = [r.to_dict() for r in result.rules]
        recommendations = [r.recommendation for r in result.rules if not r.passed and r.recommendation]
        recommendations = deduplicate_recommendations(recommendations)

        latest_sha = repo_data.commits[0].sha if repo_data.commits else ""
        repo_url = build_repo_url(owner, repo)

        report = await self.report_repo.create(
            repo_full_name=repo_data.repo.full_name,
            repo_url=repo_url,
            commit_sha=latest_sha or "head",
            score=result_dict["score"],
            grade=result_dict["grade"],
            category_breakdown=category_breakdown,
            rules=rules_data,
            recommendations=recommendations,
        )

        cache_key = f"report:{owner}/{repo}"
        await cache_service.set(cache_key, {"report_id": str(report.id)}, ttl=3600)

        logger.info("Report saved for %s/%s (id=%s)", owner, repo, report.id)
        return report

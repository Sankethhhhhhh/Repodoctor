import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Report, User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_github_id(self, github_id: int) -> User | None:
        result = await self._session.execute(select(User).where(User.github_id == github_id))
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: str) -> User | None:
        result = await self._session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def create(
        self,
        github_id: int,
        username: str,
        avatar_url: str | None = None,
    ) -> User:
        user = User(
            github_id=github_id,
            username=username,
            avatar_url=avatar_url,
        )
        self._session.add(user)
        await self._session.flush()
        return user

    async def get_or_create(
        self,
        github_id: int,
        username: str,
        avatar_url: str | None = None,
    ) -> User:
        user = await self.get_by_github_id(github_id)
        if user:
            user.username = username
            user.avatar_url = avatar_url
            return user
        return await self.create(github_id, username, avatar_url)


class ReportRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, report_id: str) -> Report | None:
        result = await self._session.execute(select(Report).where(Report.id == report_id))
        return result.scalar_one_or_none()

    async def get_by_repo_and_sha(self, repo_full_name: str, commit_sha: str) -> Report | None:
        result = await self._session.execute(
            select(Report).where(
                Report.repo_full_name == repo_full_name,
                Report.commit_sha == commit_sha,
            )
        )
        return result.scalar_one_or_none()

    async def get_user_reports(self, user_id: str, limit: int = 50) -> list[Report]:
        result = await self._session.execute(
            select(Report).where(Report.user_id == user_id).order_by(Report.created_at.desc()).limit(limit)
        )
        return list(result.scalars().all())

    async def create(
        self,
        repo_full_name: str,
        repo_url: str,
        commit_sha: str,
        score: int,
        grade: str,
        category_breakdown: dict[str, object],
        rules: list[dict[str, object]],
        recommendations: list[str],
        user_id: str | None = None,
    ) -> Report:
        report = Report(
            repo_full_name=repo_full_name,
            repo_url=repo_url,
            commit_sha=commit_sha,
            score=score,
            grade=grade,
            category_breakdown=json.dumps(category_breakdown),
            rules=json.dumps(rules),
            recommendations=json.dumps(recommendations),
            user_id=user_id,
        )
        self._session.add(report)
        await self._session.flush()
        return report

    async def delete(self, report_id: str, user_id: str) -> bool:
        report = await self.get_by_id(report_id)
        if not report or report.user_id != user_id:
            return False
        await self._session.delete(report)
        return True

    async def list_reports(self, skip: int = 0, limit: int = 20) -> list[Report]:
        result = await self._session.execute(
            select(Report).order_by(Report.created_at.desc()).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

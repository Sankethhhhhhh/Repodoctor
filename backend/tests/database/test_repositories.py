import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models.models import Base
from app.repositories.report_repo import ReportRepository, UserRepository


@pytest.fixture
async def db_session() -> AsyncSession:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


class TestUserRepository:
    @pytest.mark.asyncio
    async def test_create_user(self, db_session: AsyncSession) -> None:
        repo = UserRepository(db_session)
        user = await repo.create(
            github_id=12345,
            username="testuser",
            avatar_url="https://example.com/avatar.png",
        )
        assert user.github_id == 12345
        assert user.username == "testuser"
        assert user.id is not None

    @pytest.mark.asyncio
    async def test_get_by_github_id(self, db_session: AsyncSession) -> None:
        repo = UserRepository(db_session)
        created = await repo.create(github_id=12345, username="testuser")
        found = await repo.get_by_github_id(12345)
        assert found is not None
        assert found.id == created.id

    @pytest.mark.asyncio
    async def test_get_by_github_id_not_found(self, db_session: AsyncSession) -> None:
        repo = UserRepository(db_session)
        found = await repo.get_by_github_id(99999)
        assert found is None

    @pytest.mark.asyncio
    async def test_get_or_create_creates(self, db_session: AsyncSession) -> None:
        repo = UserRepository(db_session)
        user = await repo.get_or_create(github_id=12345, username="testuser")
        assert user.github_id == 12345
        assert user.username == "testuser"

    @pytest.mark.asyncio
    async def test_get_or_create_updates(self, db_session: AsyncSession) -> None:
        repo = UserRepository(db_session)
        await repo.create(github_id=12345, username="old_name")
        updated = await repo.get_or_create(github_id=12345, username="new_name")
        assert updated.username == "new_name"


class TestReportRepository:
    @pytest.mark.asyncio
    async def test_create_report(self, db_session: AsyncSession) -> None:
        repo = ReportRepository(db_session)
        report = await repo.create(
            repo_full_name="facebook/react",
            repo_url="https://github.com/facebook/react",
            commit_sha="abc123",
            score=85,
            grade="B",
            category_breakdown={"Testing": 18},
            rules=[{"id": "TEST", "passed": True}],
            recommendations=[],
        )
        assert report.repo_full_name == "facebook/react"
        assert report.repo_url == "https://github.com/facebook/react"
        assert report.score == 85
        assert report.grade == "B"
        assert report.id is not None

    @pytest.mark.asyncio
    async def test_get_by_id(self, db_session: AsyncSession) -> None:
        repo = ReportRepository(db_session)
        created = await repo.create(
            repo_full_name="facebook/react",
            repo_url="https://github.com/facebook/react",
            commit_sha="abc123",
            score=85,
            grade="B",
            category_breakdown={},
            rules=[],
            recommendations=[],
        )
        found = await repo.get_by_id(created.id)
        assert found is not None
        assert found.id == created.id

    @pytest.mark.asyncio
    async def test_get_by_repo_and_sha(self, db_session: AsyncSession) -> None:
        repo = ReportRepository(db_session)
        await repo.create(
            repo_full_name="facebook/react",
            repo_url="https://github.com/facebook/react",
            commit_sha="abc123",
            score=85,
            grade="B",
            category_breakdown={},
            rules=[],
            recommendations=[],
        )
        found = await repo.get_by_repo_and_sha("facebook/react", "abc123")
        assert found is not None
        assert found.commit_sha == "abc123"

    @pytest.mark.asyncio
    async def test_get_user_reports(self, db_session: AsyncSession) -> None:
        user_repo = UserRepository(db_session)
        user = await user_repo.create(github_id=12345, username="testuser")

        report_repo = ReportRepository(db_session)
        await report_repo.create(
            repo_full_name="repo1",
            repo_url="https://github.com/user/repo1",
            commit_sha="sha1",
            score=80,
            grade="B",
            category_breakdown={},
            rules=[],
            recommendations=[],
            user_id=user.id,
        )
        await report_repo.create(
            repo_full_name="repo2",
            repo_url="https://github.com/user/repo2",
            commit_sha="sha2",
            score=90,
            grade="A",
            category_breakdown={},
            rules=[],
            recommendations=[],
            user_id=user.id,
        )

        reports = await report_repo.get_user_reports(user.id)
        assert len(reports) == 2

    @pytest.mark.asyncio
    async def test_delete_report(self, db_session: AsyncSession) -> None:
        user_repo = UserRepository(db_session)
        user = await user_repo.create(github_id=12345, username="testuser")

        report_repo = ReportRepository(db_session)
        report = await report_repo.create(
            repo_full_name="repo1",
            repo_url="https://github.com/user/repo1",
            commit_sha="sha1",
            score=80,
            grade="B",
            category_breakdown={},
            rules=[],
            recommendations=[],
            user_id=user.id,
        )

        deleted = await report_repo.delete(report.id, user.id)
        assert deleted is True

        found = await report_repo.get_by_id(report.id)
        assert found is None

    @pytest.mark.asyncio
    async def test_delete_report_wrong_user(self, db_session: AsyncSession) -> None:
        user_repo = UserRepository(db_session)
        user1 = await user_repo.create(github_id=111, username="user1")
        user2 = await user_repo.create(github_id=222, username="user2")

        report_repo = ReportRepository(db_session)
        report = await report_repo.create(
            repo_full_name="repo1",
            repo_url="https://github.com/user/repo1",
            commit_sha="sha1",
            score=80,
            grade="B",
            category_breakdown={},
            rules=[],
            recommendations=[],
            user_id=user1.id,
        )

        deleted = await report_repo.delete(report.id, user2.id)
        assert deleted is False

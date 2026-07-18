import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache.service import cache_service
from app.config import settings
from app.core.database import async_session_factory, engine, get_db
from app.main import app
from app.models.models import Base


@pytest.fixture(autouse=True, scope="session")
async def _create_tables() -> None:  # type: ignore[misc]
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    return


@pytest.fixture(autouse=True)
async def _reset_rate_limit() -> None:
    settings.rate_limit_anonymous = 10000
    settings.rate_limit_authenticated = 10000
    cache_service._memory.clear()
    try:
        redis = await cache_service._get_redis()
        if redis:
            keys = await redis.keys("rate_limit:*")
            if keys:
                await redis.delete(*keys)
    except Exception:
        pass
    yield
    cache_service._memory.clear()


@pytest.fixture
async def client() -> AsyncClient:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def app_client() -> AsyncClient:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def db_session() -> AsyncSession:  # type: ignore[misc]
    async with engine.begin() as conn:
        await conn.execute(text("DELETE FROM webhook_deliveries"))
        await conn.execute(text("DELETE FROM schedules"))
        await conn.execute(text("DELETE FROM reports"))
        await conn.execute(text("DELETE FROM users"))
    async with async_session_factory() as session:

        async def _override_get_db():  # type: ignore[no-untyped-def]
            yield session

        app.dependency_overrides[get_db] = _override_get_db
        async with session.begin():
            yield session
        await session.rollback()
        app.dependency_overrides.clear()

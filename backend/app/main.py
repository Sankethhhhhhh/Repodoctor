import asyncio
import logging
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.cache.service import cache_service
from app.config import settings
from app.core.database import async_session_factory
from app.core.rate_limit import RateLimitMiddleware
from app.core.security import ETagMiddleware, RequestIDMiddleware, SecurityHeadersMiddleware
from app.logging_config import setup_logging

logger = logging.getLogger(__name__)

_scheduler_task: asyncio.Task | None = None


async def _scheduler_loop() -> None:
    while True:
        try:
            await _check_and_run_schedules()
        except Exception:
            logger.exception("Scheduler loop error")
        await asyncio.sleep(60)


async def _check_and_run_schedules() -> None:
    from app.api.report_service import ReportService
    from app.github.service import GitHubService
    from app.repositories.report_repo import ReportRepository
    from app.repositories.schedule_repo import ScheduleRepository

    async with async_session_factory() as session:
        repo = ScheduleRepository(session)
        active = await repo.list_active()
        now = datetime.now(UTC)

        for schedule in active:
            if schedule.next_run and schedule.next_run <= now:
                try:
                    github_service = GitHubService()
                    report_repo = ReportRepository(session)
                    service = ReportService(
                        github_service=github_service,
                        report_repo=report_repo,
                    )
                    await service.analyze(schedule.repo_url)
                    await github_service.close()
                    await repo.update_last_run(schedule.id, now)
                    logger.info(
                        "Scheduled scan completed for %s",
                        schedule.repo_full_name,
                    )
                except Exception:
                    logger.exception(
                        "Scheduled scan failed for %s",
                        schedule.repo_full_name,
                    )

        await session.commit()


def _validate_config() -> None:
    if settings.environment == "production" and settings.secret_key == "dev-secret-change-in-production":
        logger.critical(
            "SECRET_KEY is the default value! Set APP_SECRET_KEY for production deployments.",
        )
        sys.exit(1)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    setup_logging()
    _validate_config()
    global _scheduler_task
    _scheduler_task = asyncio.create_task(_scheduler_loop())
    yield
    _scheduler_task.cancel()
    await cache_service.close()


app = FastAPI(
    title="RepoDoctor",
    description="GitHub repository quality analysis tool",
    version=settings.version,
    lifespan=lifespan,
)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(ETagMiddleware)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "healthy", "version": settings.version}

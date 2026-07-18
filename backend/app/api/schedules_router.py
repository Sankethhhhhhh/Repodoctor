from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.github.service import parse_repo_url
from app.repositories.schedule_repo import ScheduleRepository

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

schedules_router = APIRouter(prefix="/schedules", tags=["schedules"])

FREQUENCIES = {"daily": 1, "weekly": 7, "monthly": 30}


class CreateScheduleRequest(BaseModel):
    url: str = Field(..., description="GitHub repository URL")
    frequency: str = Field(..., description="daily, weekly, or monthly")


class ScheduleResponse(BaseModel):
    id: str
    repo_full_name: str
    repo_url: str
    frequency: str
    is_active: bool
    last_run: str | None
    next_run: str
    created_at: str


class ScheduleListResponse(BaseModel):
    schedules: list[ScheduleResponse]
    total: int


@schedules_router.post("", response_model=ScheduleResponse)
async def create_schedule(
    request: CreateScheduleRequest,
    db: AsyncSession = Depends(get_db),
) -> ScheduleResponse:
    try:
        owner, repo = parse_repo_url(request.url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    if request.frequency not in FREQUENCIES:
        raise HTTPException(status_code=400, detail=f"Invalid frequency. Use: {', '.join(FREQUENCIES)}")

    repo_full_name = f"{owner}/{repo}"
    repo_url = f"https://github.com/{repo_full_name}"
    days = FREQUENCIES[request.frequency]
    next_run = datetime.now(UTC) + timedelta(days=days)

    schedule_repo = ScheduleRepository(db)
    schedule = await schedule_repo.create(
        repo_full_name=repo_full_name,
        repo_url=repo_url,
        frequency=request.frequency,
        next_run=next_run,
    )

    return ScheduleResponse(
        id=schedule.id,
        repo_full_name=schedule.repo_full_name,
        repo_url=schedule.repo_url,
        frequency=schedule.frequency,
        is_active=schedule.is_active,
        last_run=str(schedule.last_run) if schedule.last_run else None,
        next_run=str(schedule.next_run),
        created_at=str(schedule.created_at),
    )


@schedules_router.get("", response_model=ScheduleListResponse)
async def list_schedules(
    db: AsyncSession = Depends(get_db),
) -> ScheduleListResponse:
    repo = ScheduleRepository(db)
    schedules = await repo.list_active()
    return ScheduleListResponse(
        schedules=[
            ScheduleResponse(
                id=s.id,
                repo_full_name=s.repo_full_name,
                repo_url=s.repo_url,
                frequency=s.frequency,
                is_active=s.is_active,
                last_run=str(s.last_run) if s.last_run else None,
                next_run=str(s.next_run),
                created_at=str(s.created_at),
            )
            for s in schedules
        ],
        total=len(schedules),
    )


@schedules_router.delete("/{schedule_id}")
async def delete_schedule(
    schedule_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    repo = ScheduleRepository(db)
    deactivated = await repo.deactivate(schedule_id)
    if not deactivated:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return {"status": "deleted"}

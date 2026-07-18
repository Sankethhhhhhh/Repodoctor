from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Schedule


class ScheduleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        repo_full_name: str,
        repo_url: str,
        frequency: str,
        next_run: datetime,
        user_id: str | None = None,
    ) -> Schedule:
        schedule = Schedule(
            repo_full_name=repo_full_name,
            repo_url=repo_url,
            frequency=frequency,
            next_run=next_run,
            user_id=user_id,
        )
        self._session.add(schedule)
        await self._session.flush()
        return schedule

    async def get_by_id(self, schedule_id: str) -> Schedule | None:
        result = await self._session.execute(select(Schedule).where(Schedule.id == schedule_id))
        return result.scalar_one_or_none()

    async def list_active(self) -> list[Schedule]:
        result = await self._session.execute(
            select(Schedule).where(Schedule.is_active).order_by(Schedule.next_run.asc())
        )
        return list(result.scalars().all())

    async def list_user_schedules(self, user_id: str) -> list[Schedule]:
        result = await self._session.execute(
            select(Schedule).where(Schedule.user_id == user_id, Schedule.is_active).order_by(Schedule.created_at.desc())
        )
        return list(result.scalars().all())

    async def deactivate(self, schedule_id: str) -> bool:
        schedule = await self.get_by_id(schedule_id)
        if not schedule:
            return False
        schedule.is_active = False
        return True

    async def update_last_run(self, schedule_id: str, last_run: datetime) -> None:
        schedule = await self.get_by_id(schedule_id)
        if schedule:
            schedule.last_run = last_run

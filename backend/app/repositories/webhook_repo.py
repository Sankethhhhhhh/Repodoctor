from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import WebhookDelivery


class WebhookDeliveryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def exists_by_delivery_id(self, delivery_id: str) -> bool:
        result = await self._session.execute(
            select(WebhookDelivery.id).where(WebhookDelivery.delivery_id == delivery_id).limit(1)
        )
        return result.scalar_one_or_none() is not None

    async def create(
        self,
        delivery_id: str,
        event: str,
        repo_full_name: str | None = None,
        payload_summary: str | None = None,
        status: str = "received",
    ) -> WebhookDelivery:
        delivery = WebhookDelivery(
            delivery_id=delivery_id,
            event=event,
            repo_full_name=repo_full_name,
            payload_summary=payload_summary,
            status=status,
        )
        self._session.add(delivery)
        await self._session.flush()
        return delivery

    async def update_status(self, delivery_id: str, status: str) -> None:
        result = await self._session.execute(select(WebhookDelivery).where(WebhookDelivery.delivery_id == delivery_id))
        delivery = result.scalar_one_or_none()
        if delivery:
            delivery.status = status

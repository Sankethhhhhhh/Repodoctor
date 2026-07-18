from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from app.api.report_service import ReportService
from app.config import settings
from app.core.database import get_db
from app.github.service import GitHubService, parse_repo_url
from app.repositories.report_repo import ReportRepository
from app.repositories.webhook_repo import WebhookDeliveryRepository

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

webhooks_router = APIRouter(prefix="/webhooks", tags=["webhooks"])


class WebhookResponse(BaseModel):
    status: str
    message: str


class WebhookErrorResponse(BaseModel):
    error: str


@webhooks_router.post(
    "/github",
    response_model=WebhookResponse,
    responses={400: {"model": WebhookErrorResponse}, 500: {"model": WebhookErrorResponse}},
)
async def handle_github_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> WebhookResponse:
    delivery_id = request.headers.get("X-GitHub-Delivery", "")
    event = request.headers.get("X-GitHub-Event", "")
    signature = request.headers.get("X-Hub-Signature-256", "")

    if not delivery_id or not event:
        raise HTTPException(status_code=400, detail="Missing required GitHub webhook headers")

    webhook_repo = WebhookDeliveryRepository(db)
    if await webhook_repo.exists_by_delivery_id(delivery_id):
        return WebhookResponse(status="duplicate", message="Delivery already processed")

    if settings.webhook_secret and not _verify_signature(await request.body(), signature):
        await webhook_repo.create(delivery_id=delivery_id, event=event, status="signature_invalid")
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    if event == "ping":
        await webhook_repo.create(delivery_id=delivery_id, event=event, status="processed")
        return WebhookResponse(status="ok", message="pong")

    if event not in ("push", "pull_request", "release"):
        await webhook_repo.create(delivery_id=delivery_id, event=event, status="ignored")
        return WebhookResponse(status="ignored", message=f"Event '{event}' not handled")

    try:
        payload = await request.json()
    except Exception:
        payload = {}

    repo_full_name = _extract_repo_name(payload, event)
    await webhook_repo.create(
        delivery_id=delivery_id,
        event=event,
        repo_full_name=repo_full_name,
        payload_summary=f"Event: {event}, Repo: {repo_full_name}",
    )

    if repo_full_name:
        try:
            github_service = GitHubService()
            report_repo = ReportRepository(db)
            service = ReportService(github_service=github_service, report_repo=report_repo)
            owner, repo = parse_repo_url(f"https://github.com/{repo_full_name}")
            await service.analyze(f"https://github.com/{repo_full_name}")
            await github_service.close()
            await webhook_repo.update_status(delivery_id, "processed")
        except Exception:
            logger.exception("Webhook-triggered analysis failed for %s", repo_full_name)
            await webhook_repo.update_status(delivery_id, "analysis_failed")

    return WebhookResponse(status="ok", message=f"Event '{event}' processed")


def _verify_signature(body: bytes, signature: str) -> bool:
    import hashlib
    import hmac

    if not signature.startswith("sha256="):
        return False
    expected = "sha256=" + hmac.new(settings.webhook_secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def _extract_repo_name(payload: dict, event: str) -> str | None:
    if event == "push":
        repo = payload.get("repository", {})
        return repo.get("full_name")
    if event == "pull_request":
        repo = payload.get("repository", {})
        return repo.get("full_name")
    if event == "release":
        repo = payload.get("repository", {})
        return repo.get("full_name")
    return None

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


class TestWebhookPing:
    @pytest.mark.asyncio
    async def test_webhook_ping(self, client: AsyncClient, db_session: AsyncSession) -> None:
        response = await client.post(
            "/api/webhooks/github",
            content=b"{}",
            headers={
                "X-GitHub-Delivery": "test-ping-001",
                "X-GitHub-Event": "ping",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["message"] == "pong"


class TestWebhookDuplicate:
    @pytest.mark.asyncio
    async def test_webhook_duplicate(self, client: AsyncClient, db_session: AsyncSession) -> None:
        headers = {
            "X-GitHub-Delivery": "test-dup-001",
            "X-GitHub-Event": "ping",
        }
        response1 = await client.post(
            "/api/webhooks/github",
            content=b"{}",
            headers=headers,
        )
        assert response1.status_code == 200
        assert response1.json()["status"] == "ok"

        response2 = await client.post(
            "/api/webhooks/github",
            content=b"{}",
            headers=headers,
        )
        assert response2.status_code == 200
        assert response2.json()["status"] == "duplicate"


class TestWebhookMissingHeaders:
    @pytest.mark.asyncio
    async def test_webhook_missing_headers(self, client: AsyncClient, db_session: AsyncSession) -> None:
        response = await client.post(
            "/api/webhooks/github",
            content=b"{}",
        )
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data


class TestWebhookUnknownEvent:
    @pytest.mark.asyncio
    async def test_webhook_unknown_event(self, client: AsyncClient, db_session: AsyncSession) -> None:
        response = await client.post(
            "/api/webhooks/github",
            content=b"{}",
            headers={
                "X-GitHub-Delivery": "test-unknown-001",
                "X-GitHub-Event": "installation",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ignored"
        assert "installation" in data["message"]

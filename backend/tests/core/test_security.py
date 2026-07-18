import pytest
from httpx import AsyncClient


class TestSecurityHeaders:
    @pytest.mark.asyncio
    async def test_health_has_security_headers(self, client: AsyncClient) -> None:
        response = await client.get("/health")
        assert response.headers.get("X-Content-Type-Options") == "nosniff"
        assert response.headers.get("X-Frame-Options") == "DENY"
        assert response.headers.get("X-XSS-Protection") == "1; mode=block"
        assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"

    @pytest.mark.asyncio
    async def test_api_has_security_headers(self, client: AsyncClient) -> None:
        response = await client.get("/api/reports")
        assert response.headers.get("X-Content-Type-Options") == "nosniff"
        assert response.headers.get("X-Frame-Options") == "DENY"


class TestRequestID:
    @pytest.mark.asyncio
    async def test_response_has_request_id(self, client: AsyncClient) -> None:
        response = await client.get("/health")
        assert "X-Request-ID" in response.headers

    @pytest.mark.asyncio
    async def test_request_id_preserved(self, client: AsyncClient) -> None:
        response = await client.get("/health", headers={"X-Request-ID": "my-custom-id"})
        assert response.headers.get("X-Request-ID") == "my-custom-id"


class TestETag:
    @pytest.mark.asyncio
    async def test_get_has_etag(self, client: AsyncClient) -> None:
        response = await client.get("/api/reports")
        assert "ETag" in response.headers
        assert "Cache-Control" in response.headers

    @pytest.mark.asyncio
    async def test_not_modified_returns_304(self, client: AsyncClient) -> None:
        response = await client.get("/api/reports")
        etag = response.headers.get("ETag", "")
        response2 = await client.get("/api/reports", headers={"If-None-Match": etag})
        assert response2.status_code == 304

    @pytest.mark.asyncio
    async def test_different_etag_returns_200(self, client: AsyncClient) -> None:
        response = await client.get("/api/reports", headers={"If-None-Match": '"wrong-etag-value"'})
        assert response.status_code == 200

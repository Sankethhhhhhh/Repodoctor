import pytest
from httpx import AsyncClient


class TestHealthEndpoint:
    @pytest.mark.asyncio
    async def test_health(self, client: AsyncClient) -> None:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data


class TestReportsAPI:
    @pytest.mark.asyncio
    async def test_list_reports_empty(self, client: AsyncClient) -> None:
        response = await client.get("/api/reports")
        assert response.status_code == 200
        data = response.json()
        assert "reports" in data
        assert "total" in data
        assert isinstance(data["reports"], list)

    @pytest.mark.asyncio
    async def test_get_report_not_found(self, client: AsyncClient) -> None:
        response = await client.get("/api/reports/nonexistent-id")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_analyze_invalid_url(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/reports",
            json={"url": "not-a-valid-url"},
        )
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data


class TestCORS:
    @pytest.mark.asyncio
    async def test_cors_preflight(self, client: AsyncClient) -> None:
        response = await client.options(
            "/api/reports",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
            },
        )
        assert response.status_code == 200

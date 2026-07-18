import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


class TestCreateSchedule:
    @pytest.mark.asyncio
    async def test_create_schedule(self, client: AsyncClient, db_session: AsyncSession) -> None:
        response = await client.post(
            "/api/schedules",
            json={"url": "https://github.com/owner/repo", "frequency": "daily"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["repo_full_name"] == "owner/repo"
        assert data["frequency"] == "daily"
        assert data["is_active"] is True
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_schedule_invalid_url(self, client: AsyncClient, db_session: AsyncSession) -> None:
        response = await client.post(
            "/api/schedules",
            json={"url": "not-a-valid-url", "frequency": "daily"},
        )
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_create_schedule_invalid_frequency(self, client: AsyncClient, db_session: AsyncSession) -> None:
        response = await client.post(
            "/api/schedules",
            json={"url": "https://github.com/owner/repo", "frequency": "hourly"},
        )
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data


class TestListSchedules:
    @pytest.mark.asyncio
    async def test_list_schedules(self, client: AsyncClient, db_session: AsyncSession) -> None:
        await client.post(
            "/api/schedules",
            json={"url": "https://github.com/owner/repo1", "frequency": "daily"},
        )
        await client.post(
            "/api/schedules",
            json={"url": "https://github.com/owner/repo2", "frequency": "weekly"},
        )

        response = await client.get("/api/schedules")
        assert response.status_code == 200
        data = response.json()
        assert "schedules" in data
        assert "total" in data
        assert data["total"] >= 2
        repo_names = [s["repo_full_name"] for s in data["schedules"]]
        assert "owner/repo1" in repo_names
        assert "owner/repo2" in repo_names


class TestDeleteSchedule:
    @pytest.mark.asyncio
    async def test_delete_schedule(self, client: AsyncClient, db_session: AsyncSession) -> None:
        create_response = await client.post(
            "/api/schedules",
            json={"url": "https://github.com/owner/delrepo", "frequency": "monthly"},
        )
        schedule_id = create_response.json()["id"]

        delete_response = await client.delete(f"/api/schedules/{schedule_id}")
        assert delete_response.status_code == 200
        data = delete_response.json()
        assert data["status"] == "deleted"

        list_response = await client.get("/api/schedules")
        active_ids = [s["id"] for s in list_response.json()["schedules"]]
        assert schedule_id not in active_ids

    @pytest.mark.asyncio
    async def test_delete_schedule_not_found(self, client: AsyncClient, db_session: AsyncSession) -> None:
        response = await client.delete("/api/schedules/nonexistent-id")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

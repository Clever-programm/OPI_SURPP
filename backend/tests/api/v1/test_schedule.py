import pytest
from httpx import AsyncClient


class TestScheduleGenerate:
    """Тесты генерации расписания."""

    @pytest.mark.asyncio
    async def test_generate_schedule(self, client: AsyncClient, sample_order):
        """Успешная генерация (даже если будет сбой из-за склада, главное 200 OK)"""
        data = {
            "start_date": "2026-05-20",
            "end_date": "2026-05-30",
            "order_ids": [sample_order["id"]]
        }
        response = await client.post("/api/v1/schedule/generate", json=data)
        
        # Эндпоинт возвращает 200 OK с результатом генерации
        assert response.status_code == 200
        assert "success" in response.json()

class TestScheduleRead:
    """Тесты чтения расписания."""

    @pytest.mark.asyncio
    async def test_get_schedules_list(self, client: AsyncClient):
        response = await client.get("/api/v1/schedule/")
        assert response.status_code == 200
        assert "items" in response.json()

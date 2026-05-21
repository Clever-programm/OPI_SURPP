import pytest
from httpx import AsyncClient


class TestOrderCreate:
    """Тесты создания заказов."""

    @pytest.mark.asyncio
    async def test_create_order_success(self, client: AsyncClient, sample_recipe):
        """Успешное создание заказа."""
        data = {
            "due_date": "2026-12-31",
            "priority": 1,
            "items": [
                {
                    "recipe_id": sample_recipe["id"],
                    "quantity": 10
                }
            ]
        }
        response = await client.post("/api/v1/orders/", json=data)
        
        assert response.status_code == 201
        assert response.json()["status"] == "new"

class TestOrderRead:
    """Тесты чтения заказов."""

    @pytest.mark.asyncio
    async def test_get_orders_list(self, client: AsyncClient, sample_order):
        response = await client.get("/api/v1/orders/")
        assert response.status_code == 200
        assert "items" in response.json()
        assert len(response.json()["items"]) >= 1

    @pytest.mark.asyncio
    async def test_get_order_by_id(self, client: AsyncClient, sample_order):
        response = await client.get(f"/api/v1/orders/{sample_order['id']}")
        assert response.status_code == 200
        assert response.json()["id"] == sample_order["id"]

class TestOrderUpdate:
    """Тесты обновления заказов."""

    @pytest.mark.asyncio
    async def test_update_order_status(self, client: AsyncClient, sample_order):
        update_data = {"status": "planned"}
        response = await client.patch(f"/api/v1/orders/{sample_order['id']}/status", json=update_data)
        assert response.status_code == 200
        assert response.json()["status"] == "planned"

class TestOrderDelete:
    """Тесты удаления заказов."""

    @pytest.mark.asyncio
    async def test_delete_order(self, client: AsyncClient, sample_order):
        response = await client.delete(f"/api/v1/orders/{sample_order['id']}")
        assert response.status_code == 204
        
        get_resp = await client.get(f"/api/v1/orders/{sample_order['id']}")
        assert get_resp.status_code == 404

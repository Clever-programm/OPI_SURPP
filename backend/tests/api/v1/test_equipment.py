import pytest
from httpx import AsyncClient


class TestEquipmentCreate:
    """Тесты создания оборудования."""
    
    @pytest.mark.asyncio
    async def test_create_equipment_success(self, client: AsyncClient):
        """Успешное создание."""
        data = {
            "name": "Миксер промышленный",
            "quantity": 3
        }
        response = await client.post("/api/v1/equipment/", json=data)
        
        assert response.status_code == 201
        assert response.json()["name"] == "Миксер промышленный"
        assert response.json()["quantity"] == 3
    
    @pytest.mark.asyncio
    async def test_create_equipment_duplicate(self, client: AsyncClient, sample_equipment):
        """Дубликат имени (409)."""
        data = {
            "name": "Печь конвекционная",
            "quantity": 1
        }
        response = await client.post("/api/v1/equipment/", json=data)
        
        assert response.status_code == 409
    
    @pytest.mark.asyncio
    async def test_create_equipment_negative_quantity(self, client: AsyncClient):
        """Отрицательное количество (422)."""
        data = {
            "name": "Тест",
            "quantity": -5
        }
        response = await client.post("/api/v1/equipment/", json=data)
        
        assert response.status_code == 422


class TestEquipmentRead:
    """Тесты чтения оборудования."""
    
    @pytest.mark.asyncio
    async def test_get_equipment_available(self, client: AsyncClient):
        """Получение доступного оборудования."""
        # Создаём оборудование с quantity=0
        await client.post("/api/v1/equipment/", json={
            "name": "Сломанная печь",
            "quantity": 0
        })
        
        response = await client.get("/api/v1/equipment/available")
        json_data = response.json()
        
        # Сломанная печь не должна быть в списке
        for item in json_data:
            assert item["quantity"] > 0


class TestEquipmentQuantityUpdate:
    """Тесты обновления количества."""
    
    @pytest.mark.asyncio
    async def test_update_quantity_success(self, client: AsyncClient, sample_equipment):
        """Успешное обновление количества."""
        data = {"quantity": 10}
        response = await client.patch(
            f"/api/v1/equipment/{sample_equipment['id']}/quantity",
            json=data
        )
        
        assert response.status_code == 200
        assert response.json()["quantity"] == 10
    
    @pytest.mark.asyncio
    async def test_update_quantity_negative(self, client: AsyncClient, sample_equipment):
        """Отрицательное количество (422)."""
        data = {"quantity": -5}
        response = await client.patch(
            f"/api/v1/equipment/{sample_equipment['id']}/quantity",
            json=data
        )
        
        assert response.status_code == 422
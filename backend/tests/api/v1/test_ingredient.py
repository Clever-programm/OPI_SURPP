import pytest
from httpx import AsyncClient


class TestIngredientCreate:
    """Тесты создания ингредиентов."""
    
    @pytest.mark.asyncio
    async def test_create_ingredient_success(self, client: AsyncClient):
        """Успешное создание ингредиента."""
        data = {
            "name": "Сахар",
            "unit": "кг",
            "shelf_life_days": 730
        }
        response = await client.post("/api/v1/ingredients/", json=data)
        
        assert response.status_code == 201
        json_data = response.json()
        assert json_data["name"] == "Сахар"
        assert json_data["unit"] == "кг"
        assert json_data["shelf_life_days"] == 730
        assert "id" in json_data
    
    @pytest.mark.asyncio
    async def test_create_ingredient_duplicate(self, client: AsyncClient, sample_ingredient):
        """Создание дубликата имени (409 Conflict)."""
        data = {
            "name": "Мука пшеничная",  # То же имя
            "unit": "кг",
            "shelf_life_days": 365
        }
        response = await client.post("/api/v1/ingredients/", json=data)
        
        assert response.status_code == 409
        assert "уже существует" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_create_ingredient_invalid_unit(self, client: AsyncClient):
        """Некорректная единица измерения (422 Validation)."""
        data = {
            "name": "Тест",
            "unit": "недопустимая",
            "shelf_life_days": 100
        }
        response = await client.post("/api/v1/ingredients/", json=data)
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_create_ingredient_negative_shelf_life(self, client: AsyncClient):
        """Отрицательный срок годности (422 Validation)."""
        data = {
            "name": "Тест",
            "unit": "кг",
            "shelf_life_days": -10
        }
        response = await client.post("/api/v1/ingredients/", json=data)
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_create_ingredient_empty_name(self, client: AsyncClient):
        """Пустое название (422 Validation)."""
        data = {
            "name": "",
            "unit": "кг",
            "shelf_life_days": 100
        }
        response = await client.post("/api/v1/ingredients/", json=data)
        
        assert response.status_code == 422


class TestIngredientRead:
    """Тесты чтения ингредиентов."""
    
    @pytest.mark.asyncio
    async def test_get_ingredient_by_id(self, client: AsyncClient, sample_ingredient):
        """Получение ингредиента по ID."""
        response = await client.get(f"/api/v1/ingredients/{sample_ingredient['id']}")
        
        assert response.status_code == 200
        assert response.json()["name"] == "Мука пшеничная"
    
    @pytest.mark.asyncio
    async def test_get_ingredient_not_found(self, client: AsyncClient):
        """Ингредиент не найден (404)."""
        response = await client.get("/api/v1/ingredients/99999")
        
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_get_ingredients_list(self, client: AsyncClient, sample_ingredient):
        """Получение списка ингредиентов."""
        response = await client.get("/api/v1/ingredients/")
        
        assert response.status_code == 200
        json_data = response.json()
        assert "items" in json_data
        assert "total" in json_data
        assert len(json_data["items"]) >= 1
    
    @pytest.mark.asyncio
    async def test_get_ingredients_pagination(self, client: AsyncClient):
        """Пагинация списка."""
        # Создаём 10 ингредиентов
        for i in range(10):
            await client.post("/api/v1/ingredients/", json={
                "name": f"Ингредиент {i}",
                "unit": "кг",
                "shelf_life_days": 100
            })
        
        response = await client.get("/api/v1/ingredients/?page=1&limit=5")
        json_data = response.json()
        
        assert len(json_data["items"]) == 5
        assert json_data["page"] == 1
        assert json_data["limit"] == 5
        assert json_data["total"] == 10
    
    @pytest.mark.asyncio
    async def test_get_ingredients_filter_by_name(self, client: AsyncClient, sample_ingredient):
        """Фильтрация по названию."""
        response = await client.get("/api/v1/ingredients/?name=Мука пшеничная")
        json_data = response.json()
        
        assert json_data["total"] == 1
        assert json_data["items"][0]["name"] == "Мука пшеничная"
    
    @pytest.mark.asyncio
    async def test_get_ingredients_sorting(self, client: AsyncClient):
        """Сортировка списка."""
        await client.post("/api/v1/ingredients/", json={
            "name": "Абрикос",
            "unit": "кг",
            "shelf_life_days": 30
        })
        await client.post("/api/v1/ingredients/", json={
            "name": "Яблоко",
            "unit": "кг",
            "shelf_life_days": 60
        })
        
        response = await client.get("/api/v1/ingredients/?sort_by=name&sort_order=asc")
        json_data = response.json()
        
        assert json_data["items"][0]["name"] < json_data["items"][1]["name"]


class TestIngredientUpdate:
    """Тесты обновления ингредиентов."""
    
    @pytest.mark.asyncio
    async def test_update_ingredient_success(self, client: AsyncClient, sample_ingredient):
        """Успешное обновление."""
        update_data = {
            "name": "Мука пшеничная высший сорт",
            "shelf_life_days": 400
        }
        response = await client.put(
            f"/api/v1/ingredients/{sample_ingredient['id']}",
            json=update_data
        )
        
        assert response.status_code == 200
        assert response.json()["name"] == "Мука пшеничная высший сорт"
        assert response.json()["shelf_life_days"] == 400
    
    @pytest.mark.asyncio
    async def test_update_ingredient_not_found(self, client: AsyncClient):
        """Обновление несуществующего (404)."""
        response = await client.put(
            "/api/v1/ingredients/99999",
            json={"name": "Тест"}
        )
        
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_update_ingredient_duplicate_name(self, client: AsyncClient, sample_ingredient):
        """Обновление на дубликат имени (409)."""
        # Создаём второй ингредиент
        data2 = {
            "name": "Мука ржаная",
            "unit": "кг",
            "shelf_life_days": 365
        }
        resp2 = await client.post("/api/v1/ingredients/", json=data2)
        
        # Пытаемся переименовать первый во второй
        response = await client.put(
            f"/api/v1/ingredients/{sample_ingredient['id']}",
            json={"name": "Мука ржаная"}
        )
        
        assert response.status_code == 409


class TestIngredientDelete:
    """Тесты удаления ингредиентов."""
    
    @pytest.mark.asyncio
    async def test_delete_ingredient_success(self, client: AsyncClient, sample_ingredient):
        """Успешное удаление."""
        response = await client.delete(f"/api/v1/ingredients/{sample_ingredient['id']}")
        
        assert response.status_code == 204
        
        # Проверяем, что удалён
        get_response = await client.get(f"/api/v1/ingredients/{sample_ingredient['id']}")
        assert get_response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_delete_ingredient_not_found(self, client: AsyncClient):
        """Удаление несуществующего (404)."""
        response = await client.delete("/api/v1/ingredients/99999")
        
        assert response.status_code == 404


class TestIngredientCheck:
    """Тесты проверки существования."""
    
    @pytest.mark.asyncio
    async def test_check_ingredient_exists(self, client: AsyncClient, sample_ingredient):
        """Проверка существующего ингредиента."""
        response = await client.get(f"/api/v1/ingredients/check/{sample_ingredient['name']}")
        
        assert response.status_code == 200
        assert response.json()["exists"] is True
    
    @pytest.mark.asyncio
    async def test_check_ingredient_not_exists(self, client: AsyncClient):
        """Проверка несуществующего ингредиента."""
        response = await client.get("/api/v1/ingredients/check/Несуществующий")
        
        assert response.status_code == 200
        assert response.json()["exists"] is False
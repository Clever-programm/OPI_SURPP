import pytest
from httpx import AsyncClient


class TestRecipeCreate:
    """Тесты создания рецептов."""

    @pytest.mark.asyncio
    async def test_create_recipe_success(self, client: AsyncClient, sample_ingredient, sample_equipment):
        """Успешное создание рецепта."""
        data = {
            "name": "Пирожок с картошкой",
            "ingredients": [
                {
                    "ingredient_id": sample_ingredient["id"],
                    "quantity": 0.5
                }
            ],
            "operations": [
                {
                    "name": "Замес",
                    "duration_minutes": 20,
                    "sequence_number": 1,
                    "equipment_id": sample_equipment["id"],
                    "competence_id": None
                }
            ]
        }
        response = await client.post("/api/v1/recipes/", json=data)
        
        assert response.status_code == 201
        assert response.json()["name"] == "Пирожок с картошкой"


class TestRecipeRead:
    """Тесты чтения рецептов."""

    @pytest.mark.asyncio
    async def test_get_recipes_list(self, client: AsyncClient, sample_recipe):
        response = await client.get("/api/v1/recipes/")
        assert response.status_code == 200
        assert "items" in response.json()
        assert len(response.json()["items"]) >= 1

    @pytest.mark.asyncio
    async def test_get_recipe_by_id(self, client: AsyncClient, sample_recipe):
        response = await client.get(f"/api/v1/recipes/{sample_recipe['id']}")
        assert response.status_code == 200
        assert response.json()["id"] == sample_recipe["id"]
        assert "ingredients" in response.json()
        assert "operations" in response.json()


class TestRecipeUpdate:
    """Тесты обновления рецептов."""

    @pytest.mark.asyncio
    async def test_update_recipe(self, client: AsyncClient, sample_recipe):
        update_data = {"name": "Торт Прага Классический"}
        response = await client.put(f"/api/v1/recipes/{sample_recipe['id']}", json=update_data)
        assert response.status_code == 200
        assert response.json()["name"] == "Торт Прага Классический"


class TestRecipeDelete:
    """Тесты удаления рецептов."""

    @pytest.mark.asyncio
    async def test_delete_recipe(self, client: AsyncClient, sample_recipe):
        response = await client.delete(f"/api/v1/recipes/{sample_recipe['id']}")
        assert response.status_code == 204
        
        get_resp = await client.get(f"/api/v1/recipes/{sample_recipe['id']}")
        assert get_resp.status_code == 404

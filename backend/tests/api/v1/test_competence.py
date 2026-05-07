import pytest
from httpx import AsyncClient


class TestCompetenceCreate:
    """Тесты создания компетенций."""
    
    @pytest.mark.asyncio
    async def test_create_competence_success(self, client: AsyncClient):
        """Успешное создание."""
        data = {
            "name": "Кондитер 4 разряда",
            "description": "Сложные десерты"
        }
        response = await client.post("/api/v1/competences/", json=data)
        
        assert response.status_code == 201
        assert response.json()["name"] == "Кондитер 4 разряда"
    
    @pytest.mark.asyncio
    async def test_create_competence_duplicate(self, client: AsyncClient, sample_competence):
        """Дубликат имени (409)."""
        data = {
            "name": "Кондитер 3 разряда",
            "description": "Другое описание"
        }
        response = await client.post("/api/v1/competences/", json=data)
        
        assert response.status_code == 409
    
    @pytest.mark.asyncio
    async def test_create_competence_no_description(self, client: AsyncClient):
        """Создание без описания (допустимо)."""
        data = {
            "name": "Кондитер 2 разряда",
            "description": None
        }
        response = await client.post("/api/v1/competences/", json=data)
        
        assert response.status_code == 201


class TestCompetenceUpdate:
    """Тесты обновления компетенций."""
    
    @pytest.mark.asyncio
    async def test_update_competence_success(self, client: AsyncClient, sample_competence):
        """Успешное обновление."""
        update_data = {
            "description": "Обновлённое описание"
        }
        response = await client.put(
            f"/api/v1/competences/{sample_competence['id']}",
            json=update_data
        )
        
        assert response.status_code == 200
        assert response.json()["description"] == "Обновлённое описание"
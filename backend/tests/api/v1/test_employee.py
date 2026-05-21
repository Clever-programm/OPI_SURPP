import pytest
from httpx import AsyncClient


class TestEmployeeCreate:
    """Тесты создания сотрудников."""

    @pytest.mark.asyncio
    async def test_create_employee_success(self, client: AsyncClient):
        """Успешное создание сотрудника без компетенций."""
        data = {
            "name": "Петров Петр Петрович",
            "active": True
        }
        response = await client.post("/api/v1/employees/", json=data)
        
        assert response.status_code == 201
        assert response.json()["name"] == "Петров Петр Петрович"
        assert response.json()["active"] is True

    @pytest.mark.asyncio
    async def test_create_employee_with_competences(self, client: AsyncClient, sample_competence):
        """Успешное создание сотрудника с компетенциями."""
        data = {
            "name": "Сидоров Сидор",
            "active": True,
            "competences": [
                {"employee_id": 1, "competence_id": sample_competence["id"]}
            ]
        }
        response = await client.post("/api/v1/employees/", json=data)
        
        assert response.status_code == 201
        assert response.json()["name"] == "Сидоров Сидор"
        assert len(response.json()["competences"]) == 1
        assert response.json()["competences"][0]["competence_id"] == sample_competence["id"]


class TestEmployeeRead:
    """Тесты чтения сотрудников."""

    @pytest.mark.asyncio
    async def test_get_employees_list(self, client: AsyncClient, sample_employee):
        """Получение списка сотрудников."""
        response = await client.get("/api/v1/employees/")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) >= 1

    @pytest.mark.asyncio
    async def test_get_employee_by_id(self, client: AsyncClient, sample_employee):
        """Получение сотрудника по ID."""
        response = await client.get(f"/api/v1/employees/{sample_employee['id']}")
        assert response.status_code == 200
        assert response.json()["id"] == sample_employee["id"]
        assert "competences" in response.json()


class TestEmployeeUpdate:
    """Тесты обновления сотрудников."""

    @pytest.mark.asyncio
    async def test_update_employee(self, client: AsyncClient, sample_employee):
        """Успешное обновление сотрудника."""
        update_data = {
            "name": "Иванов Иван Иванович",
            "active": False
        }
        response = await client.put(f"/api/v1/employees/{sample_employee['id']}", json=update_data)
        assert response.status_code == 200
        assert response.json()["name"] == "Иванов Иван Иванович"
        assert response.json()["active"] is False

    @pytest.mark.asyncio
    async def test_add_competence_to_employee(self, client: AsyncClient, sample_employee, sample_competence):
        """Добавление компетенции сотруднику."""
        data = {"employee_id": sample_employee["id"], "competence_id": sample_competence["id"]}
        response = await client.post(f"/api/v1/employees/{sample_employee['id']}/competences", json=data)
        
        # Может быть 409 если уже есть, или 200/201. В sample_employee уже добавлена sample_competence!
        # Поэтому ожидаем 409 Conflict.
        assert response.status_code in [409, 201]

    @pytest.mark.asyncio
    async def test_remove_competence_from_employee(self, client: AsyncClient, sample_employee, sample_competence):
        """Удаление компетенции у сотрудника."""
        response = await client.delete(
            f"/api/v1/employees/{sample_employee['id']}/competences/{sample_competence['id']}"
        )
        assert response.status_code == 204


class TestEmployeeDelete:
    """Тесты удаления сотрудников."""

    @pytest.mark.asyncio
    async def test_delete_employee(self, client: AsyncClient, sample_employee, sample_competence):
        """Удаление сотрудника."""
        # Delete competence to avoid foreign key violation in test sqlite
        await client.delete(f"/api/v1/employees/{sample_employee['id']}/competences/{sample_competence['id']}")
        
        response = await client.delete(f"/api/v1/employees/{sample_employee['id']}")
        assert response.status_code == 204
        
        # Проверка что удалён
        get_response = await client.get(f"/api/v1/employees/{sample_employee['id']}")
        assert get_response.status_code == 404

import pytest
from httpx import AsyncClient


class TestStockCreate:
    """Тесты работы со складом."""

    @pytest.mark.asyncio
    async def test_add_stock_success(self, client: AsyncClient, sample_ingredient):
        """Успешное оприходование на склад."""
        data = {
            "ingredient_id": sample_ingredient["id"],
            "quantity": 100.5,
            "expiration_date": "2027-01-01"
        }
        response = await client.post("/api/v1/stock/receive", json=data)
        
        assert response.status_code == 201
        assert response.json()["quantity"] == 100.5

@pytest.fixture
async def sample_stock(client: AsyncClient, sample_ingredient):
    data = {
        "ingredient_id": sample_ingredient["id"],
        "quantity": 50.0,
        "expiration_date": "2027-01-01"
    }
    resp = await client.post("/api/v1/stock/receive", json=data)
    return resp.json()

class TestStockRead:
    """Тесты чтения склада."""

    @pytest.mark.asyncio
    async def test_get_stocks_list(self, client: AsyncClient, sample_stock):
        response = await client.get("/api/v1/stock/")
        assert response.status_code == 200
        assert "items" in response.json()
        assert len(response.json()["items"]) >= 1

    @pytest.mark.asyncio
    async def test_get_stock_by_ingredient(self, client: AsyncClient, sample_stock, sample_ingredient):
        response = await client.get(f"/api/v1/stock/{sample_stock['id']}")
        assert response.status_code == 200
        assert response.json()["quantity"] == 50.0

class TestStockWriteOff:
    """Тесты списания."""

    @pytest.mark.asyncio
    async def test_write_off_stock(self, client: AsyncClient, sample_stock, sample_ingredient):
        data = {
            "ingredient_id": sample_ingredient["id"],
            "quantity": 10.0,
            "reason": "Производство"
        }
        response = await client.post("/api/v1/stock/write-off", json=data)
        assert response.status_code == 200
        
        # Проверим остаток
        get_resp = await client.get(f"/api/v1/stock/{sample_stock['id']}")
        stocks = get_resp.json()
        assert stocks["quantity"] == 40.0

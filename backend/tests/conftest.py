import pytest
from typing import AsyncGenerator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from main import app
from app.core.database import Base
from app.api.v1.deps import get_db

# URL для SQLite в памяти
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    TEST_DATABASE_URL, 
    echo=False,
    connect_args={"check_same_thread": False}
)
async_session = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="function", autouse=True)
async def setup_database():
    """Создаёт таблицы перед каждым тестом и удаляет после."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    """Переопределяет зависимость get_db для тестов."""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@pytest.fixture(scope="function")
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Создаёт тестовый клиент с переопределённой БД."""
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest.fixture
async def sample_ingredient(client: AsyncClient):
    """Создаёт тестовый ингредиент."""
    data = {
        "name": "Мука пшеничная",
        "unit": "кг",
        "shelf_life_days": 365
    }
    response = await client.post("/api/v1/ingredients/", json=data)
    return response.json()


@pytest.fixture
async def sample_equipment(client: AsyncClient):
    """Создаёт тестовое оборудование."""
    data = {
        "name": "Печь конвекционная",
        "quantity": 2
    }
    response = await client.post("/api/v1/equipment/", json=data)
    return response.json()


@pytest.fixture
async def sample_competence(client: AsyncClient):
    """Создаёт тестовую компетенцию."""
    data = {
        "name": "Кондитер 3 разряда",
        "description": "Приготовление кремов"
    }
    response = await client.post("/api/v1/competences/", json=data)
    return response.json()
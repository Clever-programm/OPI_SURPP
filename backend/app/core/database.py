from os import getenv

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base

from app.core.config import settings

PART_URL = (
    f"{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
    f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
)

engine = create_engine(f"postgresql+psycopg2://{PART_URL}", echo=True)
async_engine = create_async_engine(f"postgresql+asyncpg://{PART_URL}", echo=settings.DEBUG, pool_pre_ping=True)

# Фабрика асинхронных сессий
async_session = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Базовый класс для моделей
Base = declarative_base()


async def get_async_session() -> AsyncSession:
    """
    Прямая функция для получения сессии.
    """
    async with async_session() as session:
        return session
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import async_session


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Асинхронная зависимость для получения сессии базы данных.
    
    Создаёт новую сессию, возвращает её, и закрывает после завершения запроса.
    Используется во всех CRUD-операциях для доступа к БД.
    
    Пример использования в эндпоинте:
        @router.get("/")
        async def read_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
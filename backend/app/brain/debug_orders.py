import asyncio
import os
import sys

# Добавляем путь к backend, чтобы импорты 'app.*' работали
sys.path.append(os.path.join(os.getcwd(), "backend"))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Пытаемся получить URL из конфига или окружения
DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres"

async def check_orders():
    engine = create_async_engine(DATABASE_URL)
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as db:
        try:
            from app.models.order import Order
            from app.models.order_item import OrderItem
            
            query = select(Order).options(selectinload(Order.items))
            result = await db.execute(query)
            orders = result.scalars().all()
            
            print(f"Total orders in DB: {len(orders)}")
            for o in orders:
                print(f"ID: {o.id}, Status: {o.status}, Due Date: {o.due_date}, Items count: {len(o.items)}")
        except Exception as e:
            print(f"Error: {e}")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_orders())

import asyncio
import logging
import os
import sys

from fastapi import FastAPI
from sqlalchemy import text
from contextlib import asynccontextmanager

from app.core.database import engine
from app.core.config import settings

logging.basicConfig(
    level=settings.LOG_LEVEL.upper(),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger("STARTUP")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Запуск
    logger.info("Запуск системы СУРПП")
    
    try:
        logger.info("Подключение к базе данных...")
        await asyncio.to_thread(check_db_connection)
        logger.info("Соединение с БД установлено")
        
        # logger.info("Применение миграций Alembic...")
        # await asyncio.to_thread(run_migrations)
        # logger.info("Миграции базы данных применены успешно")
    except Exception as e:
        logger.error(f"Ошибка при инициализации: {e}", exc_info=True)
        raise

    logger.info("Система СУРПП готова к работе")
    logger.info("=" * 50)
    
    yield

    # Остановка
    logger.info("Остановка системы СУРПП...")
    engine.dispose()
    logger.info("Соединение с БД закрыто")
    logger.info("Система СУРПП остановлена")

def check_db_connection():
    """Проверка подключения к базе данных"""
    with engine.begin() as conn:
        conn.execute(text("SELECT 1"))

def run_migrations():
    """Применение миграций Alembic"""
    from alembic.config import Config
    from alembic.script import ScriptDirectory
    from alembic.runtime.migration import MigrationContext
    from alembic import command
    
    config = Config("alembic.ini")
    script = ScriptDirectory.from_config(config)
    
    current_rev = None
    with engine.connect() as conn:
        context = MigrationContext.configure(conn)
        current_rev = context.get_current_revision()
    
    head_rev = script.get_current_head()
    
    if current_rev != head_rev:
        logger.info(f"Обновление схемы БД: {current_rev} -> {head_rev}")
        command.upgrade(config, "head")
        logger.info("Схема БД обновлена")
    else:
        logger.info("Схема БД актуальна")

app = FastAPI(
    title="СУРПП",
    description="Система управления ресурсами пищевого производства",
    version="1.0.0",
    lifespan=lifespan
    )
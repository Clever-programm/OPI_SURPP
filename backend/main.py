import asyncio
import logging
import os
import sys

from fastapi import FastAPI
from sqlalchemy import text, create_engine
from contextlib import asynccontextmanager

from app.core.database import engine, Base
from alembic.config import Config
from alembic import command
from alembic.script import ScriptDirectory
from alembic.runtime.migration import MigrationContext

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger("startup")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Запуск
    logger.info("Запуск системы СУРПП")
    
    try:
        logger.info("Подключение к базе данных...")
        await asyncio.to_thread(check_db_connection)
        logger.info("Соединение с БД установлено")
        
        logger.info("Применение миграций Alembic...")
        await asyncio.to_thread(run_migrations)
        logger.info("Миграции базы данных применены успешно")
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
    db_url = os.getenv("DB_SYNC")
    if not db_url:
        raise ValueError("DB_SYNC not found in environment")
    
    db_url = db_url.replace("asyncpg", "psycopg2")
    
    migration_engine = create_engine(db_url, pool_pre_ping=True)
    
    script = ScriptDirectory.from_config(Config("alembic.ini"))
    
    with migration_engine.begin() as conn:
        context = MigrationContext.configure(conn)
        current_rev = context.get_current_revision()
        head_rev = script.get_current_head()
        
        if current_rev != head_rev:
            logger.info(f"Обновление схемы БД: {current_rev} -> {head_rev}")
            context.run_migrations()
            logger.info("Схема БД обновлена")
        else:
            logger.info("Схема БД актуальна")
    
    migration_engine.dispose()

app = FastAPI(
    title="СУРПП",
    description="Система управления ресурсами пищевого производства",
    version="1.0.0",
    lifespan=lifespan
    )
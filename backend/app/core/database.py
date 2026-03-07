from os import getenv

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker

ASYNC_URL = getenv("DB_URL")
SYNC_URL = getenv("DB_SYNC")

engine = create_engine(SYNC_URL, echo=True)
async_engine = create_async_engine(ASYNC_URL, echo=True)
async_session = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()
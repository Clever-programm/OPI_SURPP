from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.core.database import engine, Base
from alembic.config import Config
from alembic import command
from alembic.script import ScriptDirectory
from alembic.runtime.migration import MigrationContext

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Автоматическое применение миграций при запуске
    config = Config("alembic.ini")
    script = ScriptDirectory.from_config(config)
    def upgrade(rev, context):
        return script.upgrade_revision("head", rev)
    with engine.begin() as conn:
        context = MigrationContext.configure(conn)
        if context.get_current_revision() != script.get_current_head():
            command.upgrade(config, "head")
    yield

app = FastAPI(lifespan=lifespan)
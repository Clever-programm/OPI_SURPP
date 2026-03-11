from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # На данный момент почти не используется, большинство настроек в docker-compose.yaml
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_HOST: str = "db"
    POSTGRES_PORT: str = "5432"
    POSTGRES_DB: str = "surpp_db"
    PGDATA: str ="/var/lib/postgresql/data/pgdata"
    LOG_LEVEL: str = "INFO"
    DEBUG: bool = True

    class Config:
        env_file = ".env"


settings = Settings()
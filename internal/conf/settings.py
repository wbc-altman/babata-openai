from pydantic import Field, PostgresDsn

from pkg.settings import BaseSettings


class Settings(BaseSettings):
    ENV: str = "local"

    # DB
    DB_MAIN_URLS: list[PostgresDsn] = [
        "postgresql+asyncpg://postgres:@localhost/postgres"
    ]
    DB_SUB_URLS: list[PostgresDsn] = Field(default_factory=list)
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_RECYCLE: int = 30
    DB_ECHO: bool = False

    # REDIS
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""
    REDIS_MAX_CONNECTIONS: int = 10

    # JWT
    JWT_SECRET_KEY: str = "972d2ae40f74208a33de039a52a55042"
    JWT_ALGORITHM: str = "HS256"

    # OpenAI
    API_KEY: str = ""


app_settings = Settings()

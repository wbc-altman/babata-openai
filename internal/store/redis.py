from redis.asyncio import ConnectionPool, Redis

from internal.conf.settings import app_settings

redis = Redis(
    connection_pool=ConnectionPool(
        host=app_settings.REDIS_HOST,
        port=app_settings.REDIS_HOST,
        db=app_settings.REDIS_DB,
        password=app_settings.REDIS_PASSWORD,
        max_connections=app_settings.REDIS_MAX_CONNECTIONS,
    )
)

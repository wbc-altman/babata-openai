from aiocache import RedisCache, caches


def init_cache(
    redis_host: str, redis_port: str, redis_db: str, redis_password: str, max_size: int
):
    caches.set_config(
        {
            "default": {
                "cache": "aiocache.SimpleMemoryCache",
                "serializer": {"class": "aiocache.serializers.PickleSerializer"},
            },
            "redis": {
                "cache": RedisCache,
                "endpoint": redis_host,
                "port": redis_port,
                "db": redis_db,
                "password": redis_password,
                "pool_max_size": max_size,
                "serializer": {"class": "aiocache.serializers.PickleSerializer"},
                "plugins": [],
            },
        }
    )

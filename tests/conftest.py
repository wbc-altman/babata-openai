import asyncio

import pytest
from logzero import logger
from sqlalchemy import text

from internal.conf.settings import app_settings
from internal.models import mapper_registry
from pkg.db import get_scoped_session


@pytest.fixture(scope="session")
def event_loop():
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


async def _clean_up():
    _, _, ScopeSession = get_scoped_session(
        main_engine_urls=app_settings.DB_MAIN_URLS,
        pool_size=app_settings.DB_POOL_SIZE,
        max_overflow=app_settings.DB_MAX_OVERFLOW,
        pool_recycle=app_settings.DB_POOL_RECYCLE,
        echo=app_settings.DB_ECHO,
    )
    session = ScopeSession()
    for table in mapper_registry.metadata.sorted_tables:
        truncate_sql = text(f"TRUNCATE TABLE {table.name} RESTART IDENTITY;")
        await session.execute(truncate_sql)
        await session.commit()
        logger.info(f"truncate {table.name} success !")
    await session.close()


def pytest_sessionstart(session):
    logger.info("pytest sessionstart !")
    asyncio.run(_clean_up())

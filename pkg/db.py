import asyncio
import contextvars
import functools
import os
import random
from typing import Awaitable, Callable, TypeVar

from sqlalchemy import Engine, event
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_scoped_session,
    create_async_engine,
)
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.sql import Delete, Update

from utils import json_dumps, json_loads

DB_BIND: contextvars.ContextVar[str] = contextvars.ContextVar("DB_BIND", default="")

AF = TypeVar("AF", bound=Callable[..., Awaitable])


def bind_main(func: AF) -> AF:
    async def wrapped(*args, **kwargs):
        token = DB_BIND.set("main")
        try:
            res = await func(*args, **kwargs)
        finally:
            DB_BIND.reset(token)
        return res

    return wrapped


def get_scoped_session(
    main_engine_urls: list[str],
    sub_engine_urls: list[str] | None = None,
    pool_size: int = 32,
    max_overflow: int = 10,
    pool_recycle: int = 600,  # (距最近 checkout)自动回收时间, 单位: s
    echo: bool = False,
) -> tuple[list[Engine], list[Engine], async_scoped_session]:
    """
    CAUTION: Do not share the same engine with different event loops
        if this must be the case, use another engine with poolclass=NullPool
    Ref: https://docs.sqlalchemy.org/en/14/orm/extensions/asyncio.html
    """
    main_engines = [
        create_async_engine(
            url,
            json_serializer=json_dumps,
            json_deserializer=json_loads,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_recycle=pool_recycle,
            pool_use_lifo=True,  # last in first out for reducing stale connections
            pool_pre_ping=True,  # test connection before handing out
            future=True,
            echo=echo,  # echo SQL
        )
        for url in main_engine_urls
    ]
    if sub_engine_urls:
        sub_engines = [
            create_async_engine(
                url,
                json_serializer=json_dumps,
                json_deserializer=json_loads,
                pool_size=pool_size,
                max_overflow=max_overflow,
                pool_recycle=pool_recycle,
                pool_use_lifo=True,  # last in first out for reducing stale connections
                pool_pre_ping=True,  # test connection before handing out
                future=True,
                echo=echo,  # echo SQL
            )
            for url in sub_engine_urls
        ]
    else:
        sub_engines = main_engines

    class RoutingSession(Session):
        def get_bind(self, mapper=None, clause=None, **kw):
            bind_name = DB_BIND.get()
            if (
                self._flushing
                or isinstance(clause, (Update, Delete))
                or bind_name == "main"
            ):
                return random.choice(main_engines).sync_engine
            else:
                return random.choice(sub_engines).sync_engine

    class AsyncSessionBind(AsyncSession):
        sync_session_class = RoutingSession

        async def close(self):
            DB_BIND.set("")
            return await super().close()

    session_factory = sessionmaker(expire_on_commit=False, class_=AsyncSessionBind)
    scoped_session = async_scoped_session(
        session_factory, scopefunc=asyncio.current_task
    )
    return main_engines, sub_engines, scoped_session


def get_commit_decorator(scoped_session: async_scoped_session) -> Callable:
    def commit_scope(func: AF) -> AF:  # ensure commit
        @functools.wraps(func)
        async def wrapped(*args, **kwargs):
            session: AsyncSession = scoped_session()
            try:
                res = await func(*args, **kwargs)
                await session.commit()
                return res
            except Exception:
                await session.rollback()
                raise

        return wrapped

    return commit_scope


def get_session_decorator(scoped_session: async_scoped_session) -> Callable:
    def session_scope(func: AF) -> AF:  # ensure session closure
        @functools.wraps(func)
        async def wrapped(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            finally:
                await scoped_session.remove()

        return wrapped

    return session_scope


def str_pool_status(main_engines: list[Engine], sub_engines: list[Engine] = []) -> str:
    s = "\n    Main" + "\n    Main".join(
        engine.pool.status() for engine in main_engines
    )
    if sub_engines:
        s += "\n    Sub" + "\n    Sub".join(
            engine.pool.status() for engine in sub_engines
        )
    return s


@event.listens_for(Engine, "connect")
def listen_db_connect(dbapi_connection, connection_record):
    connection_record.info["pid"] = os.getpid()


@event.listens_for(Engine, "checkout")
def listen_db_checkout(dbapi_connection, connection_record, connection_proxy):
    pid = os.getpid()
    if connection_record.info["pid"] != pid:
        _pid = connection_record.info["pid"]
        raise Exception(
            f"[_DB] checkout in wrong process {pid} | belongs to pid {_pid}"
        )

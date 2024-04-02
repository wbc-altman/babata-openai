from internal.conf.settings import app_settings
from pkg.db import get_commit_decorator, get_scoped_session, get_session_decorator

main_engines, sub_engines, ScopedSession = get_scoped_session(
    main_engine_urls=app_settings.DB_MAIN_URLS,
    sub_engine_urls=app_settings.DB_SUB_URLS,
    pool_size=app_settings.DB_POOL_SIZE,
    max_overflow=app_settings.DB_MAX_OVERFLOW,
    pool_recycle=app_settings.DB_POOL_RECYCLE,
    echo=app_settings.DB_ECHO,
)
commit_scope = get_commit_decorator(ScopedSession)
session_scope = get_session_decorator(ScopedSession)

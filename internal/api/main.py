import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.exceptions import RequestValidationError
from logzero import logger
from starlette import status
from starlette.middleware.cors import CORSMiddleware

from internal.api.endpoints.auth import router as auth_router
from internal.api.endpoints.openai import router as openai_router
from internal.conf.settings import app_settings
from pkg.cache import init_cache
from pkg.exception_handlers import (
    http_exception_handler,
    not_found_exception_handler,
    request_validation_exception_handler,
    server_error_exception_handler,
)
from pkg.exceptions import HTTPException
from pkg.middleware import RecordRequestTimeLogMiddleware

from .deps import get_session


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_cache(
        redis_host=app_settings.REDIS_HOST,
        redis_port=app_settings.REDIS_PORT,
        redis_db=app_settings.REDIS_DB,
        redis_password=app_settings.REDIS_PASSWORD,
        max_size=app_settings.REDIS_MAX_CONNECTIONS,
    )
    logger.info("startup init cache ok")

    fastapi_logger = logging.getLogger("fastapi")
    fastapi_logger.handlers = logger.handlers
    fastapi_logger.setLevel(logger.level)

    uvicorn_logger = logging.getLogger("uvicorn")
    uvicorn_logger.handlers = logger.handlers
    uvicorn_logger.setLevel(logging.WARNING)

    uvicorn_access_logger = logging.getLogger("uvicorn.access")
    uvicorn_access_logger.handlers = logger.handlers
    uvicorn_access_logger.setLevel(logging.WARNING)

    logger.info("startup logger_start_up start...")


app = FastAPI(lifespan=lifespan, dependencies=[Depends(get_session)])


def init_middlewares(app: FastAPI):
    app.add_middleware(
        CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
    )
    app.add_middleware(RecordRequestTimeLogMiddleware)
    logger.info("middleware init ok...")


def init_exception_handlers(app: FastAPI):
    app.add_exception_handler(
        status.HTTP_500_INTERNAL_SERVER_ERROR, server_error_exception_handler
    )
    app.add_exception_handler(status.HTTP_404_NOT_FOUND, not_found_exception_handler)
    app.add_exception_handler(
        RequestValidationError, request_validation_exception_handler
    )
    app.add_exception_handler(HTTPException, http_exception_handler)
    logger.info("exception handler init ok...")


init_middlewares(app)
init_exception_handlers(app)

app.include_router(openai_router, prefix="/openai", tags=["openai"])
app.include_router(auth_router, prefix="/auth", tags=["auth"])

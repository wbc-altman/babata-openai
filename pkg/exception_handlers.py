import functools

import orjson
from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import ORJSONResponse
from logzero import logger

from .exceptions import (
    HTTPException,
    NotFoundException,
    ServerException,
    ValidationException,
)


async def http_exception_handler(_: Request, exc: HTTPException):
    """特殊状态码的数据结构"""
    return ORJSONResponse(
        status_code=exc.status_code,
        content={"code": exc.code, "msg": exc.detail},
    )


async def request_validation_exception_handler(
    _req: Request, _exc: RequestValidationError
):
    exc = ValidationException()
    return ORJSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.code,
            "msg": orjson.dumps(jsonable_encoder(_exc.errors())).decode(),
        },
    )


async def server_error_exception_handler(request: Request, _exc: Exception):
    """服务器内部发生未知异常"""
    logger.error(
        f"[ExceptionHandler] InternalServerError: {request.method} {request.url.path})",
        exc_info=_exc,
    )
    exc = ServerException()
    return ORJSONResponse(
        status_code=exc.status_code,
        content={"code": exc.code, "msg": exc.detail},
    )


async def not_found_exception_handler(_req: Request, _exc: Exception):
    exc = NotFoundException()
    return ORJSONResponse(
        status_code=exc.status_code,
        content={"code": exc.code, "msg": exc.detail},
    )


def handler_client_exception():
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                res = await func(*args, **kwargs)
            except Exception as ex:
                logger.exception(
                    f"[{func.__module__}] {func.__name__}({args=}, {kwargs=}) [Failed]"
                    f" <== Error({repr(ex)})"
                )
                raise ServerException("内部服务调用异常")
            return res

        return wrapper

    return decorator

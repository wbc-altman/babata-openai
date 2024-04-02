import time

from logzero import logger
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.status import HTTP_404_NOT_FOUND


class RecordRequestTimeLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        log_info = f"{request.method} {request.url.path}"
        start_time = time.time()
        response = await call_next(request)
        cost = int((time.time() - start_time) * 1000)
        if response.status_code != HTTP_404_NOT_FOUND:
            logger.info(f"[RTL] {log_info} {response.status_code} {cost}ms")
        return response

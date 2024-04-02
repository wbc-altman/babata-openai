import asyncio
import functools
import inspect
import time
from concurrent import futures
from typing import Any, Callable

import grpc
from async_timeout import timeout
from google.protobuf.text_format import MessageToString
from grpc.aio import ServicerContext
from logzero import logger

from .exceptions import HTTPException, ServerException


async def _finally_func():
    return


class Server:
    def __init__(
        self,
        pb: object,
        servicer_cls: object,
        add_servicer_func: object,
        finally_func: Callable = _finally_func,
        rpc_timeout: int = 20,
        slow_threshold: int = 3,
        concurrency_limit: int = 256,
        thread_limit: int = 32,
    ):
        self.rpc_timeout = rpc_timeout
        self.slow_threshold = slow_threshold
        self.concurrency_limit = concurrency_limit
        self.thread_limit = thread_limit

        self.pb = pb
        self.servicer_cls = servicer_cls
        self.add_servicer_func = add_servicer_func
        self.finally_func = finally_func

    @functools.cached_property  # type: ignore
    def ErrorType(self) -> Any:  # noqa
        return getattr(self.pb, "ErrorType")

    @functools.cached_property  # type: ignore
    def Error(self) -> Any:  # noqa
        return getattr(self.pb, "Error")

    @functools.cached_property  # type: ignore
    def Response(self) -> Any:  # noqa
        return getattr(self.pb, "Response")

    def _construct_error_response(self, exc: HTTPException) -> Any:
        """Construct a pb response according to HTTPException"""
        error = self.Error(
            code=exc.code,
            description=exc.detail,
        )
        return self.Response(error=error)

    def _wrap_sync_function(self, func: Callable):
        @functools.wraps(func)
        async def wrapped(_self, request: Any, context: ServicerContext) -> Any:
            t = time.time()
            req_str = MessageToString(request, as_one_line=True)
            if len(req_str) > 128:
                req_str = f"{func.__name__}({req_str[: 128]}...)"
            else:
                req_str = f"{func.__name__}({req_str})"

            try:
                response = func(self, request, context)

                t_cost = time.time() - t
                if t_cost > self.slow_threshold * 1000:
                    logger.warning(
                        f"[RPCServer] {req_str} OK in {t_cost:.4f}s | TOO_SLOW"
                    )
                else:
                    logger.info(f"[RPCServer] {req_str} OK in {t_cost:.4f}s")
                return response

            except HTTPException as exc:
                logger.error(
                    f"[RPCServer] {req_str} ERROR in {time.time()-t:.4f}s | {exc}"
                )
                return self._construct_error_response(exc)
            except Exception:
                logger.exception(
                    f"[RPCServer] {req_str} FAILED in {time.time()-t:.4f}s"
                )
                return self._construct_error_response(ServerException)
            finally:
                await self.finally_func()

        return wrapped

    def _wrap_async_function(self, func: Callable):
        @functools.wraps(func)
        async def wrapped(_self, request: Any, context: ServicerContext) -> Any:
            t = time.time()
            req_str = MessageToString(request, as_one_line=True)
            if len(req_str) > 128:
                req_str = f"{func.__name__}({req_str[: 128]}...)"
            else:
                req_str = f"{func.__name__}({req_str})"

            try:
                async with timeout(self.rpc_timeout):
                    response = await func(self, request, context)

                t_cost = time.time() - t
                if t_cost > self.slow_threshold * 1000:
                    logger.warning(
                        f"[RPCServer] {req_str} OK in {t_cost:.4f}s | TOO_SLOW"
                    )
                else:
                    logger.info(f"[RPCServer] {req_str} OK in {t_cost:.4f}s")
                return response

            except asyncio.TimeoutError:
                logger.error(f"[RPCServer] {req_str} TIMEOUT in {time.time()-t:.4f}s")
                return self._construct_error_response(ServerException("请求超时"))
            except HTTPException as exc:
                logger.error(
                    f"[RPCServer] {req_str} ERROR in {time.time()-t:.4f}s | {exc}"
                )
                return self._construct_error_response(exc)
            except Exception:
                logger.exception(
                    f"[RPCServer] {req_str} FAILED in {time.time()-t:.4f}s"
                )
                return self._construct_error_response(ServerException)
            finally:
                await self.finally_func()

        return wrapped

    def _wrap_stream_function(self, func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapped(_self, request: Any, context: ServicerContext) -> Any:
            t = time.time()
            req_str = f"{func.__name__}"

            try:
                n_context = 0
                async for response in func(self, request, context):
                    yield response
                    n_context += 1
                logger.info(
                    f"[RPCServer] {req_str} OK in {time.time()-t:.4f}s | {n_context=}"
                )

            except HTTPException as exc:
                logger.error(
                    f"[RPCServer] {req_str} ERROR in {time.time()-t:.4f}s | {exc}"
                )
                yield self._construct_error_response(exc)
            except Exception:
                logger.exception(
                    f"[RPCServer] {req_str} FAILED in {time.time()-t:.4f}s"
                )
                yield self._construct_error_response(ServerException)
            finally:
                await self.finally_func()

        return wrapped

    async def serve(self, host: str = "0.0.0.0", port: int = 5000) -> None:
        executor = futures.ThreadPoolExecutor(max_workers=self.thread_limit)
        server = grpc.aio.server(
            migration_thread_pool=executor,
            options=(
                ("grpc.keepalive_time_ms", 10000),  # ping every 10s, default: 2h
                ("grpc.keepalive_timeout_ms", 5000),  # ping timeout in 5s, default: 20s
                # allow unlimited number of pings without data
                ("grpc.keepalive_permit_without_calls", True),
                ("grpc.http2.max_pings_without_data", 0),
                ("grpc.http2.min_time_between_pings_ms", 10000),
                ("grpc.http2.min_ping_interval_without_data_ms", 5000),
            ),
            maximum_concurrent_rpcs=self.concurrency_limit,
            # compression=grpc.Compression.Gzip,
        )

        # wrap and servicer
        def _predicate(x):
            return inspect.iscoroutinefunction(x) or inspect.isfunction(x)

        for func_name, func in inspect.getmembers(
            self.servicer_cls, predicate=_predicate
        ):
            if inspect.isasyncgenfunction(func):
                setattr(self.servicer_cls, func_name, self._wrap_stream_function(func))
            elif inspect.iscoroutinefunction(func):
                setattr(self.servicer_cls, func_name, self._wrap_async_function(func))
            else:
                setattr(self.servicer_cls, func_name, self._wrap_sync_function(func))

        servicer = self.servicer_cls()
        self.add_servicer_func(servicer, server)
        server.add_insecure_port(f"{host}:{port}")
        logger.info(f"[RPCServer] wrap and add servicer OK, now listen at {port}")

        await server.start()
        await server.wait_for_termination()

import asyncio

from logzero import logger

from internal.store.db import ScopedSession, main_engines, sub_engines
from pkg.db import str_pool_status
from pkg.grpc_server import Server
from utils import sample_in_rate

from .pb import babata_openai_pb2, babata_openai_pb2_grpc
from .servicer import BabataOpenAIServicer


def serve(port: int = 5000):
    async def _finally_func():
        await ScopedSession.remove()
        if sample_in_rate(0.05):
            logger.info(
                f"[RPCServer.Pool]5%{str_pool_status(main_engines, sub_engines)}"
            )

    server = Server(
        babata_openai_pb2,
        BabataOpenAIServicer,
        babata_openai_pb2_grpc.add_BabataOpenAIServicer_to_server,
        _finally_func,
    )
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(server.serve(port=port))
    finally:
        loop.close()


if __name__ == "__main__":
    serve()

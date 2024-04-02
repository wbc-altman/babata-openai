from concurrent import futures

import grpc
import pytest_asyncio

from internal.grpc.pb import babata_openai_pb2_grpc
from internal.grpc.servicer import BabataOpenAIServicer


@pytest_asyncio.fixture(scope="session")
async def grpc_server(event_loop):
    server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=1))
    babata_openai_pb2_grpc.add_BabataOpenAIServicer_to_server(
        BabataOpenAIServicer(), server
    )
    server.add_insecure_port("[::]:5000")
    await server.start()
    yield server
    await server.stop(None)


@pytest_asyncio.fixture(scope="session")
async def grpc_client(grpc_server):
    channel = grpc.aio.insecure_channel(f"localhost:5000")
    client = babata_openai_pb2_grpc.BabataOpenAIStub(channel)
    yield client
    await channel.close()

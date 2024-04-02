from contextlib import asynccontextmanager

import grpc

from client.pb import babata_openai_protos, babata_openai_services


@asynccontextmanager
async def babata_openai_client() -> babata_openai_services.BabataOpenAIStub:
    async with grpc.aio.insecure_channel("127.0.0.1:5000") as channel:
        stub = babata_openai_services.BabataOpenAIStub(channel)
        yield stub


async def ping():
    async with babata_openai_client() as client:
        res = await client.Ping(
            babata_openai_protos.PingRequest(),
            timeout=3,
        )
        print(res.pong)

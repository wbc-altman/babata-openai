import pytest

from internal.grpc import pb


@pytest.mark.asyncio
async def test_ping(grpc_client):
    res = await grpc_client.Ping(request=pb.PingRequest())
    assert res.pong is True

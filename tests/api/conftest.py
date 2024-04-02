import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from logzero import logger

from internal.api import app
from internal.models import T_Account
from internal.store.db import ScopedSession
from utils import get_password_hash


@pytest_asyncio.fixture(scope="session")
async def http_client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test/"
    ) as client:
        logger.info("Http Client is ready")
        yield client


@pytest_asyncio.fixture
def account_data():
    return {
        "username": "admin",
        "password": "123456",
    }


@pytest_asyncio.fixture
async def remove_t_account(account_data: dict):
    yield
    session = ScopedSession()
    account = await T_Account.get_object_or_none(
        T_Account.username == account_data["username"]
    )
    await account.delete()
    await session.commit()


@pytest_asyncio.fixture
async def add_t_account(account_data: dict):
    session = ScopedSession()
    obj = T_Account(**account_data)
    obj.password = get_password_hash(obj.password)

    session.add(obj)
    await session.commit()
    logger.info("admin_t_account create success")
    yield obj
    await session.delete(obj)
    await session.commit()
    logger.info("admin_t_account delete success")


@pytest_asyncio.fixture
async def token_headers(http_client: AsyncClient, account_data):
    response = await http_client.post(
        "/auth/login",
        json=account_data,
    )
    access_token = response.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}
    return headers

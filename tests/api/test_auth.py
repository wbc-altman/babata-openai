import pytest
from httpx import AsyncClient
from logzero import logger

from internal.models import T_Account


class TestAuth:
    @pytest.mark.asyncio
    async def test_register(
        self, http_client: AsyncClient, account_data: dict, remove_t_account
    ):
        response = await http_client.post(
            "/auth/register",
            json=account_data,
        )
        logger.info(f"test_register: {response.json()}")
        assert response.status_code == 200
        assert response.json()["data"]["username"] == account_data["username"]

    @pytest.mark.asyncio
    async def test_login(
        self,
        http_client: AsyncClient,
        add_t_account: T_Account,
        account_data: dict,
    ):
        response = await http_client.post(
            "/auth/login",
            json=account_data,
        )
        logger.info(f"test_login: {response.json()}")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_profile(
        self, http_client: AsyncClient, add_t_account: T_Account, token_headers: dict
    ):
        response = await http_client.get(
            "/auth/profile",
            headers=token_headers,
        )
        logger.info(f"test_profile: {response.json()}")
        assert response.status_code == 200
        assert response.json()["data"]["username"] == add_t_account.username

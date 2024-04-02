from openai import AsyncClient

from internal.conf.settings import app_settings

openai_client = AsyncClient(
    api_key=app_settings.API_KEY,
    base_url="https://api.moonshot.cn/v1",
)

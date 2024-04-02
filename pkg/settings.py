import orjson
from pydantic import BaseSettings as PydanticBaseSettings


class BaseSettings(PydanticBaseSettings):
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

        json_loads = orjson.loads
        json_dumps = orjson.dumps

        underscore_attrs_are_private = True  # _为私有属性，不做赋值
        validate_assignment = True  # 赋值校验

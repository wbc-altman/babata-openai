import enum
from typing import Generic, TypeVar

from pydantic import BaseModel, Field
from pydantic.generics import GenericModel

T = TypeVar("T")


class Code(enum.IntEnum):
    SUCCESS: int = 0

    # user error
    VALIDATION_ERROR: int = 40000
    UNAUTHORIZED: int = 40001
    PERMISSION_ERROR: int = 40003
    NOT_FOUND: int = 40004

    # server error
    SERVER_ERROR: int = 50000


class Response(GenericModel, Generic[T]):
    code: Code = Code.SUCCESS
    msg: str = "success"
    data: T | None


class Page(BaseModel):
    page: int = Field(default=1, ge=1)
    size: int = Field(default=10, ge=1)


class PageInfo(Page):
    total: int


class PageResponse(GenericModel, Generic[T]):
    code: Code = Code.SUCCESS
    msg: str = "success"
    data: T | None
    page_info: PageInfo

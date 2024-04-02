from pydantic import BaseModel

from .base import DatetimeBaseModel


class Token(BaseModel):
    access_token: str
    expires_in: int = 7200
    token_type: str = "bearer"


class AccountOut(DatetimeBaseModel):
    id: int
    username: str

    class Config:
        orm_mode = True

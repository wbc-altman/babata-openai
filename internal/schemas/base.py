from datetime import datetime

from pydantic import BaseModel, validator


class DatetimeBaseModel(BaseModel):
    created_at: int
    updated_at: int

    @validator("created_at", "updated_at", pre=True)
    def pre_datetime(cls, value: int | datetime):
        if isinstance(value, datetime):
            return int(value.timestamp())
        return value

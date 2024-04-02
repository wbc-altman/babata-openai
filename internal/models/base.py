import datetime
from typing import Optional, Type, TypeVar
from uuid import UUID as UUIDType
from uuid import uuid4

from fastapi.encoders import jsonable_encoder
from logzero import logger
from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Integer,
    String,
    TypeDecorator,
    select,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, declarative_mixin, registry

from internal.store.db import ScopedSession
from utils import local_now

mapper_registry = registry()


class IntEnum(TypeDecorator):
    impl = Integer
    cache_ok = True

    def __init__(self, enumtype, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._enumtype = enumtype

    def process_bind_param(self, value, _):
        return value

    def process_result_value(self, value, _):
        try:
            return self._enumtype(value)
        except Exception as ex:
            logger.warning(f"Invalid enum value {value}, error: {ex}")
            return self._enumtype(0)


class StringEnum(TypeDecorator):
    impl = String
    cache_ok = True

    def __init__(self, enumtype, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._enumtype = enumtype

    def process_bind_param(self, value, _):
        return value

    def process_result_value(self, value, _):
        try:
            return self._enumtype(value)
        except Exception as ex:
            logger.warning(f"Invalid enum value {value}, error: {ex}")
            return self._enumtype("unknown")


class UInt64(TypeDecorator):
    impl = BigInteger
    cache_ok = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def process_bind_param(self, value, _):
        if value >= (1 << 63):
            return value - (1 << 64)
        return value

    def process_result_value(self, value, _):
        if value < 0:
            return value + (1 << 64)
        return value


T = TypeVar("T", bound="BaseMixin")

XT = TypeVar("XT")


@declarative_mixin
class BaseMixin:
    id: Mapped[int] = Column(BigInteger, primary_key=True)
    uuid: Mapped[UUIDType] = Column(UUID(as_uuid=True), unique=True, default=uuid4)

    meta_info: Mapped[dict] = Column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime.datetime] = Column(
        DateTime(timezone=True),
        nullable=False,
        default=local_now,
    )
    updated_at: Mapped[datetime.datetime] = Column(
        DateTime(timezone=True),
        nullable=False,
        default=local_now,
        onupdate=local_now,
    )
    deleted_at: Mapped[Optional[datetime.datetime]] = Column(
        DateTime(timezone=True), default=None
    )

    def xvalue_and_record(
        self, attribute: str, value_from: XT, value_to: XT, source: str
    ) -> None:
        record_name = f"{attribute}_records"
        if record_name not in self.meta_info:
            self.meta_info[record_name] = []
        if hasattr(value_from, "name"):
            _value_from = value_from.name.lower()
            _value_to = value_to.name.lower()
        else:
            _value_from = value_from
            _value_to = value_to
        self.meta_info[record_name].append(
            {
                "at": local_now(),
                "by": source,
                "from": _value_from,
                "to": _value_to,
            }
        )
        self.__setattr__(attribute, value_to)

    @property
    def created_at_ts(self) -> int:
        return int(self.created_at.timestamp())

    @classmethod
    async def get(cls: Type[T], pk: int) -> Optional[T]:
        instance = await ScopedSession().get(cls, pk)
        return instance

    @classmethod
    async def mget(cls: Type[T], *pks: int) -> dict[int, T]:
        if not pks:
            return {}

        query = await ScopedSession().execute(select(cls).where(cls.id.in_(pks)))
        return {t.id: t for t in query.scalars().all()}

    @classmethod
    async def query_objects(cls: Type[T], *conditions, filter_delete=True) -> list[T]:
        conditions = list(conditions)
        if filter_delete:
            conditions.append(cls.deleted_at.is_(None))
        statement = select(cls).where(*conditions)
        result = await ScopedSession().scalars(statement)
        return result.all()

    @classmethod
    async def query_object_or_none(
        cls: Type[T], *conditions, filter_delete=True
    ) -> Optional[T]:
        conditions = list(conditions)
        if filter_delete:
            conditions.append(cls.deleted_at.is_(None))
        statement = select(cls).where(*conditions)
        result = await ScopedSession().scalar(statement)
        return result

    @classmethod
    async def get_object_or_none(
        cls: Type[T], filter_delete=True, **kwargs
    ) -> Optional[T]:
        statement = select(cls).filter_by(**kwargs)
        if filter_delete:
            statement = statement.where(cls.deleted_at.is_(None))
        result = await ScopedSession().scalar(statement)
        return result

    async def delete(self, auto_commit: bool = True) -> bool:
        if self.deleted_at is not None:
            return False
        self.deleted_at = local_now()
        if auto_commit:
            session = ScopedSession()
            session.add(self)
            await session.commit()
            await session.refresh(self)
        return True

    async def update(self, update_data: dict) -> None:
        if not update_data:
            return None
        obj_data = jsonable_encoder(self)
        for field in obj_data:
            if field in update_data:
                setattr(self, field, update_data[field])
        session = ScopedSession()
        session.add(self)
        await session.commit()
        await session.refresh(self)
        return None

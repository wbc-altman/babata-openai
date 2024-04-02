from __future__ import annotations

from sqlalchemy import Column, String
from sqlalchemy.orm import Mapped

from .base import BaseMixin, mapper_registry


@mapper_registry.mapped
class T_Account(BaseMixin):
    __tablename__ = "t_account"

    username: Mapped[str] = Column(String, nullable=False)
    password: Mapped[str] = Column(String, nullable=False)

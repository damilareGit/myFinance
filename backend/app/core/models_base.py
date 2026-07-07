"""Shared SQLAlchemy declarative base — every model in every submodule
inherits from this one `Base` so `Base.metadata.create_all` creates all
tables in a single call."""
from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass

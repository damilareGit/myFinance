"""Categories are data, not an enum, so users can create their own and the
same generic backend serves any country/bank without a code change.

`user_id = NULL` means "global default" — visible to every user. A
per-user row shadows nothing; it's simply an additional option/rule
available only to that user, layered on top of the globals.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ..core.models_base import Base

# income: counts toward total_income. expense: counts toward total_spend.
# transfer: neither (loan disbursements, moving money between own accounts).
CategoryKind = str  # "income" | "expense" | "transfer"


class CategoryRecord(Base):
    __tablename__ = "categories"
    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_category_user_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    kind: Mapped[str] = mapped_column(String(20))  # income | expense | transfer
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class CategoryRule(Base):
    __tablename__ = "category_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), index=True)
    keyword: Mapped[str] = mapped_column(String(200))  # matched as a case-insensitive substring
    priority: Mapped[int] = mapped_column(Integer, default=100)  # lower checked first
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

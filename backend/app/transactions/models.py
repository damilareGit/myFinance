"""SQLAlchemy models for persisted transactions.

Two tables:

- `transactions` — one row per parsed/manual transaction, scoped by
  `user_id`. `tx_hash` is the stable dedup key from `hashing.transaction_hash`.
  `category_id/name/kind` are denormalized from `categories.CategoryRecord`
  at write time — cheap to keep in sync since categorization only happens
  on insert, and it avoids a join on every dashboard read.
- `category_overrides` — one row per user correction. Kept separate from
  `transactions` rather than an UPDATE-in-place, so re-parsing a statement
  never silently wipes out a correction: overrides are applied as a join
  at read time, in `repository.get_transactions`.
"""
from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ..core.models_base import Base


class TransactionRecord(Base):
    __tablename__ = "transactions"
    __table_args__ = (UniqueConstraint("user_id", "tx_hash", name="uq_transactions_user_hash"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    tx_hash: Mapped[str] = mapped_column(String(24), index=True)

    date: Mapped[date] = mapped_column(Date, index=True)
    description: Mapped[str] = mapped_column(String(500))
    debit: Mapped[float] = mapped_column(Float, default=0.0)
    credit: Mapped[float] = mapped_column(Float, default=0.0)
    balance: Mapped[float | None] = mapped_column(Float, nullable=True)
    account: Mapped[str] = mapped_column(String(100))
    currency: Mapped[str] = mapped_column(String(10), default="NGN")

    category_id: Mapped[int] = mapped_column(Integer, index=True)
    category_name: Mapped[str] = mapped_column(String(100))
    category_kind: Mapped[str] = mapped_column(String(20))

    source_page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source: Mapped[str] = mapped_column(String(20), default="statement")  # "statement" | "manual"

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class CategoryOverride(Base):
    __tablename__ = "category_overrides"
    __table_args__ = (UniqueConstraint("user_id", "tx_hash", name="uq_overrides_user_hash"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    tx_hash: Mapped[str] = mapped_column(String(24), index=True)
    category_id: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class UploadLog(Base):
    """One row per uploaded file — mostly for surfacing parse warnings
    and letting a user see their upload history."""
    __tablename__ = "upload_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    filename: Mapped[str] = mapped_column(String(255))
    account_detected: Mapped[str] = mapped_column(String(100))
    rows_parsed: Mapped[int] = mapped_column(Integer)
    rows_new: Mapped[int] = mapped_column(Integer)
    fallback_used: Mapped[bool] = mapped_column(default=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

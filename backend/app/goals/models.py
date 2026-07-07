"""Goals are tracked manually in this first cut: the user tells us how
much they've saved/paid off so far (`current_amount`) rather than us
inferring it from linked transaction categories. Auto-linking a goal to a
category (e.g. "Savings & Investments") and deriving progress from actual
transfers is a natural next step, but it requires deciding how to handle
multiple goals sharing one category and is deferred until there's a real
need for it.
"""
from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ..core.models_base import Base


class GoalRecord(Base):
    __tablename__ = "goals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)

    name: Mapped[str] = mapped_column(String(150))
    kind: Mapped[str] = mapped_column(String(20))  # "savings" | "debt"
    target_amount: Mapped[float] = mapped_column(Float)
    current_amount: Mapped[float] = mapped_column(Float, default=0.0)
    target_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    currency: Mapped[str] = mapped_column(String(10), default="NGN")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

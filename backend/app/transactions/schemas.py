"""Data models for parsed/manual bank transactions and summaries.

`category_*` fields are denormalized copies of the matching `CategoryRecord`
(id/name/kind) rather than a foreign-key join, so this module — which is
deliberately framework/DB-agnostic like the rest of the aggregates layer —
never needs to touch the categories table directly.
"""
from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class Transaction(BaseModel):
    date: date
    description: str
    debit: float = 0.0
    credit: float = 0.0
    balance: Optional[float] = None
    account: str = "Statement"
    currency: str = "NGN"
    category_id: int
    category_name: str
    category_kind: str  # "income" | "expense" | "transfer"
    source_page: Optional[int] = None
    tx_hash: str = ""  # populated by hashing.transaction_hash() — stable key for category corrections

    @property
    def is_income(self) -> bool:
        return self.category_kind == "income"

    @property
    def is_spend(self) -> bool:
        return self.category_kind == "expense"


class ParseWarning(BaseModel):
    page: Optional[int] = None
    message: str


class CategoryTotal(BaseModel):
    category_id: int
    category_name: str
    category_kind: str
    debit: float
    credit: float


class MonthlySummary(BaseModel):
    month: str  # "YYYY-MM"
    income: float
    spend: float
    savings_contributed: float
    min_balance: Optional[float] = None
    savings_rate_pct: float

    @classmethod
    def build(cls, month: str, income: float, spend: float, savings_contributed: float,
              min_balance: Optional[float]) -> "MonthlySummary":
        rate = 0.0 if income <= 0 else 100.0 * (income - spend) / income
        return cls(
            month=month, income=income, spend=spend,
            savings_contributed=savings_contributed,
            min_balance=min_balance, savings_rate_pct=round(rate, 1),
        )


class Insight(BaseModel):
    tone: str  # "good" | "warn" | "neutral"
    message: str


class StatementAnalysis(BaseModel):
    transactions: list[Transaction]
    category_totals: list[CategoryTotal]
    monthly_summaries: list[MonthlySummary]
    insights: list[Insight]
    total_income: float
    total_spend: float
    overall_savings_rate_pct: float
    primary_currency: str = "NGN"
    warnings: list[ParseWarning] = Field(default_factory=list)

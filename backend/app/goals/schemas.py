from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class GoalCreate(BaseModel):
    name: str
    kind: str  # "savings" | "debt"
    target_amount: float = Field(gt=0)
    current_amount: float = 0.0
    target_date: Optional[date] = None
    currency: str = "NGN"


class GoalUpdate(BaseModel):
    name: Optional[str] = None
    target_amount: Optional[float] = Field(default=None, gt=0)
    current_amount: Optional[float] = None
    target_date: Optional[date] = None


class GoalOut(BaseModel):
    id: int
    name: str
    kind: str
    target_amount: float
    current_amount: float
    remaining_amount: float
    progress_pct: float
    target_date: Optional[date]
    currency: str
    pace_message: Optional[str] = None

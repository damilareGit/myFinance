from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.deps import get_current_user_id
from ..core.db import get_session
from ..transactions.aggregates import build_monthly_summaries
from ..transactions.repository import get_transactions
from . import service
from .schemas import GoalCreate, GoalOut, GoalUpdate

router = APIRouter()


async def _avg_monthly_savings(session: AsyncSession, user_id: int) -> float | None:
    transactions = await get_transactions(session, user_id)
    if not transactions:
        return None
    monthly = build_monthly_summaries(transactions)
    recent = monthly[-3:]  # last up to 3 months on record
    if not recent:
        return None
    return sum(m.savings_contributed for m in recent) / len(recent)


@router.get("", response_model=list[GoalOut])
async def list_goals(
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(get_current_user_id),
) -> list[GoalOut]:
    goals = await service.list_goals(session, user_id)
    avg_savings = await _avg_monthly_savings(session, user_id)
    return [service.to_goal_out(g, avg_savings) for g in goals]


@router.post("", response_model=GoalOut)
async def create_goal(
    body: GoalCreate,
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(get_current_user_id),
) -> GoalOut:
    if body.kind not in ("savings", "debt"):
        raise HTTPException(400, "kind must be 'savings' or 'debt'.")
    goal = await service.create_goal(session, user_id, body)
    await session.commit()
    avg_savings = await _avg_monthly_savings(session, user_id)
    return service.to_goal_out(goal, avg_savings)


@router.patch("/{goal_id}", response_model=GoalOut)
async def update_goal(
    goal_id: int,
    body: GoalUpdate,
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(get_current_user_id),
) -> GoalOut:
    goal = await service.get_goal(session, user_id, goal_id)
    if goal is None:
        raise HTTPException(404, "Goal not found.")
    goal = await service.update_goal(goal, body)
    await session.commit()
    avg_savings = await _avg_monthly_savings(session, user_id)
    return service.to_goal_out(goal, avg_savings)


@router.delete("/{goal_id}")
async def delete_goal(
    goal_id: int,
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(get_current_user_id),
) -> dict:
    goal = await service.get_goal(session, user_id, goal_id)
    if goal is None:
        raise HTTPException(404, "Goal not found.")
    await service.delete_goal(session, goal)
    await session.commit()
    return {"status": "deleted"}

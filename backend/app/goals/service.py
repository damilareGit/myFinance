from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import GoalRecord
from .schemas import GoalCreate, GoalOut, GoalUpdate


def _pace_message(goal: GoalRecord, avg_monthly_savings: float | None) -> str | None:
    """Only estimated for savings goals — debt payoff pace would need a
    per-month breakdown of the Debt Payment category, which the
    transactions module doesn't compute today (see build_monthly_summaries)."""
    if goal.kind != "savings":
        return None
    remaining = goal.target_amount - goal.current_amount
    if remaining <= 0:
        return "Goal reached — nice work."
    if not avg_monthly_savings or avg_monthly_savings <= 0:
        return None

    months = remaining / avg_monthly_savings
    if goal.target_date:
        months_until_target = (goal.target_date.year - date.today().year) * 12 + (
            goal.target_date.month - date.today().month
        )
        if months <= max(months_until_target, 0):
            return f"On pace for {goal.target_date.strftime('%B %Y')} at your recent savings rate."
        return f"At your recent savings rate you'd reach this ~{months:.0f} months late — consider raising the monthly contribution."
    return f"About {months:.0f} months to go at your recent savings rate."


def to_goal_out(goal: GoalRecord, avg_monthly_savings: float | None) -> GoalOut:
    remaining = max(goal.target_amount - goal.current_amount, 0.0)
    pct = 0.0 if goal.target_amount <= 0 else min(100.0, round(goal.current_amount / goal.target_amount * 100, 1))
    return GoalOut(
        id=goal.id,
        name=goal.name,
        kind=goal.kind,
        target_amount=goal.target_amount,
        current_amount=goal.current_amount,
        remaining_amount=round(remaining, 2),
        progress_pct=pct,
        target_date=goal.target_date,
        currency=goal.currency,
        pace_message=_pace_message(goal, avg_monthly_savings),
    )


async def list_goals(session: AsyncSession, user_id: int) -> list[GoalRecord]:
    result = await session.execute(
        select(GoalRecord).where(GoalRecord.user_id == user_id).order_by(GoalRecord.created_at)
    )
    return list(result.scalars().all())


async def create_goal(session: AsyncSession, user_id: int, body: GoalCreate) -> GoalRecord:
    goal = GoalRecord(
        user_id=user_id,
        name=body.name.strip(),
        kind=body.kind,
        target_amount=body.target_amount,
        current_amount=body.current_amount,
        target_date=body.target_date,
        currency=body.currency,
    )
    session.add(goal)
    await session.flush()
    return goal


async def get_goal(session: AsyncSession, user_id: int, goal_id: int) -> GoalRecord | None:
    goal = await session.get(GoalRecord, goal_id)
    if goal is None or goal.user_id != user_id:
        return None
    return goal


async def update_goal(goal: GoalRecord, body: GoalUpdate) -> GoalRecord:
    if body.name is not None:
        goal.name = body.name.strip()
    if body.target_amount is not None:
        goal.target_amount = body.target_amount
    if body.current_amount is not None:
        goal.current_amount = body.current_amount
    if body.target_date is not None:
        goal.target_date = body.target_date
    return goal


async def delete_goal(session: AsyncSession, goal: GoalRecord) -> None:
    await session.delete(goal)

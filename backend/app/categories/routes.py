from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.deps import get_current_user_id
from ..core.db import get_session
from . import service

router = APIRouter()


class CategoryResponse(BaseModel):
    id: int
    name: str
    kind: str
    is_custom: bool


class RuleResponse(BaseModel):
    id: int
    category_id: int
    keyword: str
    is_custom: bool


class CreateCategoryRequest(BaseModel):
    name: str
    kind: str  # "income" | "expense" | "transfer"


class CreateRuleRequest(BaseModel):
    keyword: str


@router.get("", response_model=list[CategoryResponse])
async def get_categories(
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(get_current_user_id),
) -> list[CategoryResponse]:
    records = await service.list_categories(session, user_id)
    return [
        CategoryResponse(id=r.id, name=r.name, kind=r.kind, is_custom=r.user_id is not None)
        for r in records
    ]


@router.post("", response_model=CategoryResponse)
async def create_category(
    body: CreateCategoryRequest,
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(get_current_user_id),
) -> CategoryResponse:
    if body.kind not in ("income", "expense", "transfer"):
        raise HTTPException(400, "kind must be one of: income, expense, transfer.")
    try:
        record = await service.create_user_category(session, user_id, body.name.strip(), body.kind)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    await session.commit()
    return CategoryResponse(id=record.id, name=record.name, kind=record.kind, is_custom=True)


@router.delete("/{category_id}")
async def delete_category(
    category_id: int,
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(get_current_user_id),
) -> dict:
    try:
        await service.delete_user_category(session, user_id, category_id)
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc
    await session.commit()
    return {"status": "deleted"}


@router.get("/rules", response_model=list[RuleResponse])
async def get_rules(
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(get_current_user_id),
) -> list[RuleResponse]:
    rules = await service.list_rules(session, user_id)
    return [
        RuleResponse(id=r.id, category_id=r.category_id, keyword=r.keyword, is_custom=r.user_id is not None)
        for r in rules
    ]


@router.post("/{category_id}/rules")
async def create_rule(
    category_id: int,
    body: CreateRuleRequest,
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(get_current_user_id),
) -> dict:
    if not body.keyword.strip():
        raise HTTPException(400, "keyword cannot be empty.")
    try:
        rule = await service.add_user_rule(session, user_id, category_id, body.keyword)
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc
    await session.commit()
    return {"id": rule.id, "category_id": rule.category_id, "keyword": rule.keyword}


@router.delete("/rules/{rule_id}")
async def delete_rule(
    rule_id: int,
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(get_current_user_id),
) -> dict:
    try:
        await service.delete_user_rule(session, user_id, rule_id)
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc
    await session.commit()
    return {"status": "deleted"}

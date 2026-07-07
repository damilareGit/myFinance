"""DB-driven replacement for the old static-keyword-list categorizer.

Rules are loaded once per request (`load_rules`) rather than per
transaction, then matched in plain Python — cheap, and keeps the hot loop
free of DB round trips when categorizing a whole statement.
"""
from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import CategoryRecord, CategoryRule


@dataclass
class CategoryInfo:
    id: int
    name: str
    kind: str


@dataclass
class RuleSet:
    # ordered (priority, then id) list of (keyword, category)
    rules: list[tuple[str, CategoryInfo]]
    other_income: CategoryInfo
    uncategorized: CategoryInfo


async def load_rules(session: AsyncSession, user_id: int) -> RuleSet:
    result = await session.execute(
        select(CategoryRule, CategoryRecord)
        .join(CategoryRecord, CategoryRule.category_id == CategoryRecord.id)
        .where((CategoryRule.user_id.is_(None)) | (CategoryRule.user_id == user_id))
        .order_by(CategoryRule.priority, CategoryRule.id)
    )
    rules: list[tuple[str, CategoryInfo]] = []
    categories_by_name: dict[str, CategoryInfo] = {}
    for rule, category in result.all():
        info = CategoryInfo(id=category.id, name=category.name, kind=category.kind)
        categories_by_name[category.name] = info
        rules.append((rule.keyword.lower(), info))

    for fallback_name in ("Other Income", "Uncategorized"):
        if fallback_name not in categories_by_name:
            existing = await session.execute(
                select(CategoryRecord).where(CategoryRecord.user_id.is_(None), CategoryRecord.name == fallback_name)
            )
            record = existing.scalar_one()
            categories_by_name[fallback_name] = CategoryInfo(id=record.id, name=record.name, kind=record.kind)

    return RuleSet(
        rules=rules,
        other_income=categories_by_name["Other Income"],
        uncategorized=categories_by_name["Uncategorized"],
    )


def categorize(rule_set: RuleSet, description: str, debit: float, credit: float) -> CategoryInfo:
    d = description.lower()
    for keyword, category in rule_set.rules:
        if keyword and keyword in d:
            return category
    if credit > 0 and debit == 0:
        return rule_set.other_income
    return rule_set.uncategorized


async def list_categories(session: AsyncSession, user_id: int) -> list[CategoryRecord]:
    result = await session.execute(
        select(CategoryRecord)
        .where((CategoryRecord.user_id.is_(None)) | (CategoryRecord.user_id == user_id))
        .order_by(CategoryRecord.kind, CategoryRecord.name)
    )
    return list(result.scalars().all())


async def create_user_category(session: AsyncSession, user_id: int, name: str, kind: str) -> CategoryRecord:
    existing = await session.execute(
        select(CategoryRecord).where(CategoryRecord.user_id == user_id, CategoryRecord.name == name)
    )
    if existing.scalar_one_or_none() is not None:
        raise ValueError(f"You already have a category named '{name}'.")
    record = CategoryRecord(user_id=user_id, name=name, kind=kind)
    session.add(record)
    await session.flush()
    return record


async def add_user_rule(session: AsyncSession, user_id: int, category_id: int, keyword: str) -> CategoryRule:
    category = await session.get(CategoryRecord, category_id)
    if category is None or (category.user_id is not None and category.user_id != user_id):
        raise ValueError("Category not found.")
    rule = CategoryRule(user_id=user_id, category_id=category_id, keyword=keyword.strip())
    session.add(rule)
    await session.flush()
    return rule


async def list_rules(session: AsyncSession, user_id: int) -> list[CategoryRule]:
    """Global rules plus this user's own — for the management UI, not the
    categorizer hot path (see `load_rules` for that)."""
    result = await session.execute(
        select(CategoryRule)
        .where((CategoryRule.user_id.is_(None)) | (CategoryRule.user_id == user_id))
        .order_by(CategoryRule.category_id, CategoryRule.priority, CategoryRule.id)
    )
    return list(result.scalars().all())


async def delete_user_rule(session: AsyncSession, user_id: int, rule_id: int) -> None:
    rule = await session.get(CategoryRule, rule_id)
    if rule is None or rule.user_id != user_id:
        # Global rules (user_id is None) are shared defaults, not owned by
        # any one user — deliberately not deletable from here.
        raise ValueError("Rule not found.")
    await session.delete(rule)
    await session.flush()


async def delete_user_category(session: AsyncSession, user_id: int, category_id: int) -> None:
    category = await session.get(CategoryRecord, category_id)
    if category is None or category.user_id != user_id:
        raise ValueError("Category not found.")
    own_rules = await session.execute(
        select(CategoryRule).where(CategoryRule.category_id == category_id, CategoryRule.user_id == user_id)
    )
    for rule in own_rules.scalars().all():
        await session.delete(rule)
    await session.delete(category)
    await session.flush()

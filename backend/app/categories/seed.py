"""Seed data for categories and keyword rules.

Two layers, both idempotent (safe to call on every startup):

1. `seed_global_defaults` — a generalized, country-agnostic category set
   with a modest starter keyword list. Every user sees these.
2. `seed_personal_nigeria_rules` — the keyword list this app was
   originally tuned against (tithe, IKEDC, Cowrywise, Nigerian salary-
   advance lenders, ...). Scoped to a single `user_id` so it doesn't
   leak into other family members' generalized defaults. Most of these
   rules attach to the *global* categories (e.g. "ikedc" -> global
   "Utilities") — only the keyword is Nigeria-specific, not the category.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import CategoryRecord, CategoryRule

# name -> (kind, [keywords])
GLOBAL_DEFAULT_CATEGORIES: dict[str, tuple[str, list[str]]] = {
    "Salary": ("income", ["salary", "payroll"]),
    "Other Income": ("income", []),  # fallback for unmatched credits, no keywords of its own
    "Loan/Credit Received": ("transfer", ["loan disbursal", "loan disbursement", "principal disbursement"]),
    "Internal Transfer": ("transfer", ["self transfer", "own account transfer"]),
    "Housing/Rent": ("expense", ["rent", "mortgage"]),
    "Utilities": ("expense", ["electric", "water bill", "gas bill", "internet bill", "waste management"]),
    "Communication & Subscriptions": ("expense", ["airtime", "mobile data", "subscription", "streaming"]),
    "Food & Groceries": ("expense", ["restaurant", "grocery", "groceries", "supermarket"]),
    "Transport": ("expense", ["uber", "bolt", "taxi", "fuel", "fare"]),
    "Health": ("expense", ["pharmacy", "hospital", "clinic", "medical"]),
    "Insurance": ("expense", ["insurance premium"]),
    "Debt Payment": ("expense", ["loan repayment", "loan payment", "credit card payment"]),
    "Savings & Investments": ("expense", ["savings", "investment", "mutual fund"]),
    "Entertainment": ("expense", ["cinema", "netflix", "spotify"]),
    "Shopping": ("expense", ["amazon", "online shopping"]),
    "Personal Care": ("expense", ["salon", "barbershop", "spa"]),
    "Education": ("expense", ["school fees", "tuition"]),
    "Family & Dependents": ("expense", ["child support", "dependent"]),
    "Giving/Charity": ("expense", ["donation", "charity"]),
    "Bank Fees": ("expense", ["bank fee", "service charge", "maintenance fee"]),
    "Cash Withdrawal": ("expense", ["atm withdrawal", "cash withdrawal"]),
    "Uncategorized": ("expense", []),  # fallback for unmatched debits, no keywords of its own
}

# category name -> extra keywords, layered onto the global category as a
# rule scoped to a single user_id (see seed_personal_nigeria_rules below)
PERSONAL_NIGERIA_RULES: dict[str, list[str]] = {
    "Salary": ["month allowance", "13th month"],
    "Loan/Credit Received": [],
    "Giving/Charity": ["tithe", "offering", "church"],
    "Housing/Rent": ["mortgage board"],
    "Savings & Investments": [
        "cowrywise", "money market", "mmf", "bamboo", "stanbic ibtc money",
        "unitedcapital", "gt money mkt", "invest.proce", "stocks",
    ],
    "Family & Dependents": [
        "welfare", "refund", "loanrefund", "cash loan", "cashloan",
        "holdbody", "hold body", "diaper", "tiara", "uniform", "schoolbus",
    ],
    "Health": ["hmo", "wrytemed", "nett pharmacy", "medication"],
    "Utilities": [
        "ikedc", "power unit", "home internet", "internet subscription",
        "gas refill", "waste mgt", "wastemgt", "lawma",
    ],
    "Communication & Subscriptions": ["mtn", "airtel", "mobile bills"],
    "Transport": ["indrive", "shuttlers"],
    "Food & Groceries": ["food", "lunch", "dinner", "shawarma", "chicken republic", "spar", "staples", "snacks", "kitchen", "chowdeck"],
    "Cash Withdrawal": ["atm cash wdl"],
    "Debt Payment": [
        "oxygen x", "pstkdirectdebit", "management fee", "credit life insurance",
        "disbursement charges", "principal liquidation", "pdlp",
    ],
    "Bank Fees": [
        "sms alert", "stamp dut", "vatcharges", "vat charges",
        "commission on nip", "txn_fee", "transfer charges",
        "electronic money transfer levy", "value added tax",
    ],
    "Education": ["school", "tuition"],
    "Shopping": ["temu", "jumia", "apple.com", "google play", "web pymt", "pos pymt", "pos pur", "posweb purchase"],
    "Personal Care": ["haircut", "affirmations studio"],
}


async def _get_or_create_category(session: AsyncSession, user_id: int | None, name: str, kind: str) -> CategoryRecord:
    existing = await session.execute(
        select(CategoryRecord).where(CategoryRecord.user_id == user_id, CategoryRecord.name == name)
    )
    record = existing.scalar_one_or_none()
    if record is not None:
        return record
    record = CategoryRecord(user_id=user_id, name=name, kind=kind)
    session.add(record)
    await session.flush()
    return record


async def seed_global_defaults(session: AsyncSession) -> None:
    for name, (kind, keywords) in GLOBAL_DEFAULT_CATEGORIES.items():
        category = await _get_or_create_category(session, None, name, kind)
        for keyword in keywords:
            existing = await session.execute(
                select(CategoryRule).where(
                    CategoryRule.user_id.is_(None),
                    CategoryRule.category_id == category.id,
                    CategoryRule.keyword == keyword,
                )
            )
            if existing.scalar_one_or_none() is None:
                session.add(CategoryRule(user_id=None, category_id=category.id, keyword=keyword))
    await session.commit()


async def seed_personal_nigeria_rules(session: AsyncSession, user_id: int) -> None:
    for category_name, keywords in PERSONAL_NIGERIA_RULES.items():
        if not keywords:
            continue
        category = await session.execute(
            select(CategoryRecord).where(CategoryRecord.user_id.is_(None), CategoryRecord.name == category_name)
        )
        category_record = category.scalar_one_or_none()
        if category_record is None:
            continue  # global defaults not seeded yet; caller should seed globals first
        for keyword in keywords:
            existing = await session.execute(
                select(CategoryRule).where(
                    CategoryRule.user_id == user_id,
                    CategoryRule.category_id == category_record.id,
                    CategoryRule.keyword == keyword,
                )
            )
            if existing.scalar_one_or_none() is None:
                session.add(CategoryRule(user_id=user_id, category_id=category_record.id, keyword=keyword))
    await session.flush()

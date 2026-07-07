"""Persistence operations for transactions and category overrides.

Design choice: overrides are never written back into
`transactions.category_id`. They're stored separately and applied as a
read-time join. This means re-uploading or re-parsing a statement can
never silently erase a correction — the override always wins regardless
of what the categorizer produces on a later run.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..categories.models import CategoryRecord
from .hashing import transaction_hash
from .models import CategoryOverride, TransactionRecord, UploadLog
from .schemas import Transaction


async def save_transactions(
    session: AsyncSession,
    user_id: int,
    transactions: list[Transaction],
    filename: str = "",
    fallback_used: bool = False,
    source: str = "statement",
) -> tuple[int, int]:
    """Insert new transactions for a user, skipping ones already stored.

    Returns (rows_parsed, rows_new).
    """
    if not transactions:
        return (0, 0)

    hashes = [transaction_hash(t) for t in transactions]
    existing_rows = await session.execute(
        select(TransactionRecord.tx_hash).where(
            TransactionRecord.user_id == user_id,
            TransactionRecord.tx_hash.in_(hashes),
        )
    )
    existing_hashes = {row[0] for row in existing_rows}

    new_count = 0
    for t, h in zip(transactions, hashes):
        if h in existing_hashes:
            continue
        session.add(TransactionRecord(
            user_id=user_id,
            tx_hash=h,
            date=t.date,
            description=t.description,
            debit=t.debit,
            credit=t.credit,
            balance=t.balance,
            account=t.account,
            currency=t.currency,
            category_id=t.category_id,
            category_name=t.category_name,
            category_kind=t.category_kind,
            source_page=t.source_page,
            source=source,
        ))
        existing_hashes.add(h)  # guard against duplicates within the same upload/entry
        new_count += 1

    if source == "statement":
        session.add(UploadLog(
            user_id=user_id,
            filename=filename,
            account_detected=transactions[0].account if transactions else "Statement",
            rows_parsed=len(transactions),
            rows_new=new_count,
            fallback_used=fallback_used,
        ))

    await session.flush()
    return (len(transactions), new_count)


async def set_category_override(session: AsyncSession, user_id: int, tx_hash: str, category_id: int) -> None:
    existing = await session.execute(
        select(CategoryOverride).where(
            CategoryOverride.user_id == user_id,
            CategoryOverride.tx_hash == tx_hash,
        )
    )
    row = existing.scalar_one_or_none()
    if row:
        row.category_id = category_id
    else:
        session.add(CategoryOverride(user_id=user_id, tx_hash=tx_hash, category_id=category_id))
    await session.flush()


async def get_transactions(session: AsyncSession, user_id: int) -> list[Transaction]:
    """Fetch all of a user's transactions with overrides applied.

    This is the single read path the analysis/dashboard layer should use —
    never read straight from `TransactionRecord` elsewhere, or overrides
    will be silently skipped.
    """
    tx_rows = await session.execute(
        select(TransactionRecord).where(TransactionRecord.user_id == user_id).order_by(TransactionRecord.date)
    )
    records = tx_rows.scalars().all()
    if not records:
        return []

    override_rows = await session.execute(
        select(CategoryOverride.tx_hash, CategoryOverride.category_id).where(CategoryOverride.user_id == user_id)
    )
    overrides = {h: cid for h, cid in override_rows.all()}

    # Overrides only store a category_id — resolve name/kind for any
    # category_id referenced by an override so we don't have to join per row.
    override_category_ids = set(overrides.values())
    category_lookup: dict[int, CategoryRecord] = {}
    if override_category_ids:
        cat_rows = await session.execute(
            select(CategoryRecord).where(CategoryRecord.id.in_(override_category_ids))
        )
        category_lookup = {c.id: c for c in cat_rows.scalars().all()}

    transactions: list[Transaction] = []
    for r in records:
        override_id = overrides.get(r.tx_hash)
        if override_id is not None and override_id in category_lookup:
            cat = category_lookup[override_id]
            category_id, category_name, category_kind = cat.id, cat.name, cat.kind
        else:
            category_id, category_name, category_kind = r.category_id, r.category_name, r.category_kind

        transactions.append(Transaction(
            date=r.date,
            description=r.description,
            debit=r.debit,
            credit=r.credit,
            balance=r.balance,
            account=r.account,
            currency=r.currency,
            category_id=category_id,
            category_name=category_name,
            category_kind=category_kind,
            source_page=r.source_page,
            tx_hash=r.tx_hash,
        ))
    return transactions


async def delete_all_for_user(session: AsyncSession, user_id: int) -> None:
    """Full reset — mirrors the "Clear all data" button in the browser prototype."""
    for model in (TransactionRecord, CategoryOverride, UploadLog):
        rows = await session.execute(select(model).where(model.user_id == user_id))
        for row in rows.scalars().all():
            await session.delete(row)
    await session.flush()

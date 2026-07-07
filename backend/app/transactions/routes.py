"""Transaction ingestion + analysis endpoints.

Endpoints:
    POST   /transactions/upload            — parse + persist one statement PDF, return full analysis
    POST   /transactions/upload-batch      — same, for multiple files
    POST   /transactions/manual            — add one manually-entered transaction (e.g. cash purchase)
    GET    /transactions/analysis          — recompute analysis from everything stored so far
    PATCH  /transactions/{tx_hash}/category — correct a transaction's category
    DELETE /transactions/all               — wipe this user's data
"""
from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.deps import get_current_user_id
from ..categories import service as category_service
from ..core.db import get_session
from .aggregates import analyze
from .hashing import transaction_hash
from .parser import RawStatement, StatementParseError, _clean_amount, _parse_date, parse_statement
from .repository import delete_all_for_user, get_transactions, save_transactions, set_category_override
from .schemas import StatementAnalysis, Transaction

router = APIRouter()


async def _rows_to_transactions(session: AsyncSession, user_id: int, raw: RawStatement) -> list[Transaction]:
    rule_set = await category_service.load_rules(session, user_id)
    transactions: list[Transaction] = []
    for row in raw.rows:
        parsed_date = _parse_date(row.posted_date)
        if parsed_date is None:
            continue
        debit = _clean_amount(row.debit)
        credit = _clean_amount(row.credit)
        balance = _clean_amount(row.balance)
        category = category_service.categorize(rule_set, row.description, debit, credit)
        t = Transaction(
            date=parsed_date,
            description=row.description,
            debit=debit,
            credit=credit,
            balance=balance if balance else None,
            account=raw.account_hint,
            category_id=category.id,
            category_name=category.name,
            category_kind=category.kind,
            source_page=row.page,
        )
        t.tx_hash = transaction_hash(t)
        transactions.append(t)
    return transactions


async def _persist_and_reanalyze(
    session: AsyncSession,
    user_id: int,
    new_transactions: list[Transaction],
    filename: str,
    fallback_used: bool,
    source: str = "statement",
) -> StatementAnalysis:
    await save_transactions(session, user_id, new_transactions, filename=filename, fallback_used=fallback_used, source=source)
    await session.commit()
    all_transactions = await get_transactions(session, user_id)
    return analyze(all_transactions)


@router.post("/upload", response_model=StatementAnalysis)
async def upload_statement(
    file: UploadFile,
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(get_current_user_id),
) -> StatementAnalysis:
    if file.content_type not in ("application/pdf", "application/x-pdf"):
        raise HTTPException(400, "Please upload a PDF statement.")
    try:
        raw = parse_statement(file.file)
    except StatementParseError as exc:
        raise HTTPException(422, str(exc)) from exc

    new_transactions = await _rows_to_transactions(session, user_id, raw)
    if not new_transactions:
        raise HTTPException(422, "No transactions could be read from this statement.")

    return await _persist_and_reanalyze(session, user_id, new_transactions, file.filename or "", raw.fallback_used)


@router.post("/upload-batch", response_model=StatementAnalysis)
async def upload_statements_batch(
    files: list[UploadFile],
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(get_current_user_id),
) -> StatementAnalysis:
    all_new: list[Transaction] = []
    errors: list[str] = []

    for file in files:
        if file.content_type not in ("application/pdf", "application/x-pdf"):
            errors.append(f"{file.filename}: not a PDF, skipped.")
            continue
        try:
            raw = parse_statement(file.file)
            txs = await _rows_to_transactions(session, user_id, raw)
            all_new.extend(txs)
            await save_transactions(session, user_id, txs, filename=file.filename or "", fallback_used=raw.fallback_used)
        except StatementParseError as exc:
            errors.append(f"{file.filename}: {exc}")

    if not all_new and errors:
        raise HTTPException(422, "No transactions could be read from any uploaded file. " + " ".join(errors))

    await session.commit()
    all_transactions = await get_transactions(session, user_id)
    return analyze(all_transactions)


class ManualTransactionRequest(BaseModel):
    date: date
    description: str
    amount: float  # positive = money out (debit), negative = money in (credit)
    account: str = "Cash"
    currency: str = "NGN"
    category_id: int | None = None  # if omitted, auto-categorized from description


@router.post("/manual", response_model=StatementAnalysis)
async def add_manual_transaction(
    body: ManualTransactionRequest,
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(get_current_user_id),
) -> StatementAnalysis:
    debit = max(body.amount, 0.0)
    credit = max(-body.amount, 0.0)

    if body.category_id is not None:
        categories = await category_service.list_categories(session, user_id)
        match = next((c for c in categories if c.id == body.category_id), None)
        if match is None:
            raise HTTPException(404, "Category not found.")
        category_id, category_name, category_kind = match.id, match.name, match.kind
    else:
        rule_set = await category_service.load_rules(session, user_id)
        category = category_service.categorize(rule_set, body.description, debit, credit)
        category_id, category_name, category_kind = category.id, category.name, category.kind

    t = Transaction(
        date=body.date,
        description=body.description,
        debit=debit,
        credit=credit,
        balance=None,
        account=body.account,
        currency=body.currency,
        category_id=category_id,
        category_name=category_name,
        category_kind=category_kind,
        source_page=None,
    )
    t.tx_hash = transaction_hash(t)

    return await _persist_and_reanalyze(session, user_id, [t], filename="", fallback_used=False, source="manual")


@router.get("/analysis", response_model=StatementAnalysis)
async def get_analysis(
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(get_current_user_id),
) -> StatementAnalysis:
    """Recompute the dashboard from everything stored for this user so far.

    Call this on dashboard load — don't cache the analysis payload
    anywhere, since it must reflect the latest category overrides.
    """
    transactions = await get_transactions(session, user_id)
    if not transactions:
        raise HTTPException(404, "No transactions yet — upload a statement or add one manually.")
    return analyze(transactions)


class CategoryCorrectionRequest(BaseModel):
    category_id: int


@router.patch("/{tx_hash}/category")
async def correct_category(
    tx_hash: str,
    body: CategoryCorrectionRequest,
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(get_current_user_id),
) -> dict:
    await set_category_override(session, user_id, tx_hash, body.category_id)
    await session.commit()
    return {"tx_hash": tx_hash, "category_id": body.category_id}


@router.delete("/all")
async def clear_all_data(
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(get_current_user_id),
) -> dict:
    await delete_all_for_user(session, user_id)
    await session.commit()
    return {"status": "cleared"}

"""Turn a list of categorized Transactions into summaries and plain-language
wealth-building insights.

Kept deliberately free of any web-framework or database imports so it can
be unit-tested and reused outside the API layer (e.g. in a notebook or a
scheduled job that recomputes insights nightly).
"""
from __future__ import annotations

from collections import defaultdict

from .schemas import (
    CategoryTotal,
    Insight,
    MonthlySummary,
    StatementAnalysis,
    Transaction,
)


def _month_key(t: Transaction) -> str:
    return f"{t.date.year:04d}-{t.date.month:02d}"


def _dominant_currency(transactions: list[Transaction]) -> str:
    counts: dict[str, int] = defaultdict(int)
    for t in transactions:
        counts[t.currency] += 1
    return max(counts, key=counts.get) if counts else "NGN"


def build_category_totals(transactions: list[Transaction]) -> list[CategoryTotal]:
    totals: dict[int, list] = {}  # category_id -> [name, kind, debit, credit]
    for t in transactions:
        row = totals.setdefault(t.category_id, [t.category_name, t.category_kind, 0.0, 0.0])
        row[2] += t.debit
        row[3] += t.credit
    return [
        CategoryTotal(category_id=cid, category_name=name, category_kind=kind, debit=round(d, 2), credit=round(c, 2))
        for cid, (name, kind, d, c) in sorted(totals.items(), key=lambda kv: -kv[1][2])
    ]


def build_monthly_summaries(transactions: list[Transaction]) -> list[MonthlySummary]:
    by_month: dict[str, dict] = defaultdict(lambda: {"income": 0.0, "spend": 0.0, "savings": 0.0, "min_balance": None})
    for t in transactions:
        m = by_month[_month_key(t)]
        if t.category_kind == "income":
            m["income"] += t.credit
        if t.category_kind == "expense":
            m["spend"] += t.debit
        if t.category_name == "Savings & Investments":
            m["savings"] += t.debit
        if t.balance is not None and t.balance > 0:
            m["min_balance"] = t.balance if m["min_balance"] is None else min(m["min_balance"], t.balance)

    return [
        MonthlySummary.build(
            month=m,
            income=round(v["income"], 2),
            spend=round(v["spend"], 2),
            savings_contributed=round(v["savings"], 2),
            min_balance=round(v["min_balance"], 2) if v["min_balance"] is not None else None,
        )
        for m, v in sorted(by_month.items())
    ]


def generate_insights(
    transactions: list[Transaction],
    category_totals: list[CategoryTotal],
    monthly_summaries: list[MonthlySummary],
    currency: str,
) -> list[Insight]:
    insights: list[Insight] = []
    totals_by_name = {ct.category_name: ct for ct in category_totals}

    total_income = sum(ct.credit for ct in category_totals if ct.category_kind == "income")
    savings_debit = totals_by_name.get("Savings & Investments", CategoryTotal(
        category_id=0, category_name="Savings & Investments", category_kind="expense", debit=0, credit=0
    )).debit
    savings_rate = (savings_debit / total_income * 100) if total_income > 0 else 0.0

    if savings_rate >= 15:
        insights.append(Insight(
            tone="good",
            message=(
                f"You directed {savings_rate:.1f}% of income into savings/investment "
                "categories — a solid rate. The next lever is consistency, not size."
            ),
        ))
    else:
        insights.append(Insight(
            tone="warn",
            message=(
                f"Only {savings_rate:.1f}% of income went into savings/investment "
                "categories. Pushing this toward 15-20% would compound meaningfully "
                "over a year — worth looking at money market funds or similar "
                "liquid, interest-bearing options available in your market."
            ),
        ))

    debt_payment = totals_by_name.get("Debt Payment")
    if debt_payment and debt_payment.debit > 0:
        insights.append(Insight(
            tone="warn",
            message=(
                f"Loan/debt payment activity totalled {currency} {debt_payment.debit:,.0f}. "
                "Short-term or salary-advance loans often carry a flat fee regardless of "
                "tenor — cheap-looking in absolute terms, expensive annualized. Worth "
                "checking if a small standing emergency buffer could replace some of this."
            ),
        ))

    if monthly_summaries:
        last = monthly_summaries[-1]
        if last.min_balance is not None and last.income > 0 and last.min_balance < last.income * 0.05:
            insights.append(Insight(
                tone="warn",
                message=(
                    f"Balance dropped below 5% of monthly income in {last.month} "
                    f"(lowest seen: {currency} {last.min_balance:,.0f}). Running this close "
                    "to zero before the next income means any delay or surprise expense "
                    "becomes a crisis. A 1-2 month buffer in a liquid account fixes this."
                ),
            ))

    giving = totals_by_name.get("Giving/Charity")
    if giving and total_income > 0:
        insights.append(Insight(
            tone="neutral",
            message=(
                f"Giving/charity came to {giving.debit / total_income * 100:.1f}% of "
                "income — consistent and easy to plan around if it's a fixed percentage."
            ),
        ))

    return insights


def analyze(transactions: list[Transaction]) -> StatementAnalysis:
    """Compute the full StatementAnalysis payload for a set of transactions."""
    category_totals = build_category_totals(transactions)
    monthly = build_monthly_summaries(transactions)
    currency = _dominant_currency(transactions)
    insights = generate_insights(transactions, category_totals, monthly, currency)

    total_income = sum(ct.credit for ct in category_totals if ct.category_kind == "income")
    total_spend = sum(ct.debit for ct in category_totals if ct.category_kind == "expense")
    overall_rate = 0.0 if total_income <= 0 else round(100 * (total_income - total_spend) / total_income, 1)

    return StatementAnalysis(
        transactions=transactions,
        category_totals=category_totals,
        monthly_summaries=monthly,
        insights=insights,
        total_income=round(total_income, 2),
        total_spend=round(total_spend, 2),
        overall_savings_rate_pct=overall_rate,
        primary_currency=currency,
    )

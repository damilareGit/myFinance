"""Parse Nigerian bank statement PDFs into structured transactions.

Two extraction strategies, tried in order:

1. Table extraction (pdfplumber, line-based grid detection) — works when
   the PDF has real ruled table lines. This is the primary path and is
   what's been validated against Access Bank and GTBank statements.
2. Generic line-reconstruction fallback — for statements with no ruled
   grid. Groups words by y-position into visual lines, then walks them
   looking for a leading date and trailing debit/credit/balance amounts.
   Less reliable, but keeps the parser from failing outright on an
   unfamiliar bank format.

Both paths return the same normalized dict shape so callers don't need
to know which strategy fired.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import BinaryIO, Union

import pdfplumber

_DATE_PATTERNS = [
    "%d-%b-%y",   # 25-JUN-25
    "%d-%b-%Y",   # 01-Jan-2026
    "%d/%m/%Y",
    "%d/%m/%y",
]

_AMOUNT_RE = re.compile(r"^-$|^\d{1,3}(,\d{3})*(\.\d+)?$")
_DATE_TOKEN_RE = re.compile(r"^\d{1,2}[-/][A-Za-z]{3}[-/]\d{2,4}$")


class StatementParseError(Exception):
    pass


@dataclass
class RawRow:
    posted_date: str
    description: str
    debit: str
    credit: str
    balance: str
    page: int


@dataclass
class RawStatement:
    account_hint: str
    rows: list[RawRow] = field(default_factory=list)
    pages_processed: int = 0
    fallback_used: bool = False


def _clean_amount(token: str) -> float:
    token = (token or "").strip()
    if token in ("", "-", "nan"):
        return 0.0
    try:
        return float(token.replace(",", ""))
    except ValueError:
        return 0.0


def _parse_date(token: str) -> date | None:
    token = (token or "").strip()
    for fmt in _DATE_PATTERNS:
        try:
            return datetime.strptime(token, fmt).date()
        except ValueError:
            continue
    return None


def _detect_account_hint(sample_text: str) -> str:
    s = sample_text.lower()
    # Domain/footer markers first — these only appear in a statement's own
    # letterhead/footer, unlike bank names which can show up incidentally
    # inside transaction descriptions (e.g. "...GSIRecovery...BY GUARANTY
    # TRUST BANK PLC" on someone else's Access Bank statement).
    domain_markers = [
        ("accessbankplc.com", "Access Bank"),
        ("gtbank.com", "GTBank"),
        ("gtworld", "GTBank"),
        ("guaranty trust bank ltd systems and control group", "GTBank"),
        ("zenithbank.com", "Zenith Bank"),
        ("firstbanknigeria.com", "First Bank"),
        ("ubagroup.com", "UBA"),
    ]
    for marker, name in domain_markers:
        if marker in s:
            return name
    # Fall back to generic name mentions only if no stronger marker matched
    generic_markers = [
        ("guaranty trust", "GTBank"),
        ("gtbank", "GTBank"),
        ("gtco", "GTBank"),
        ("access bank", "Access Bank"),
        ("access holdings", "Access Bank"),
        ("zenith", "Zenith Bank"),
        ("first bank", "First Bank"),
        ("firstbank", "First Bank"),
        ("united bank for africa", "UBA"),
    ]
    for marker, name in generic_markers:
        if marker in s:
            return name
    return "Statement"


# ---------------------------------------------------------------------------
# Strategy 1: ruled-table extraction
# ---------------------------------------------------------------------------

# Maps a lowercased header row (first few cells) to a column-index layout.
# index order: posted_date, description, debit, credit, balance
_KNOWN_HEADERS: dict[tuple[str, ...], tuple[int, int, int, int, int]] = {
    ("posted date", "value date", "description", "debit (ngn)", "credit (ngn)", "balance (ngn)"): (0, 2, 3, 4, 5),
    ("trans. date", "value. date", "reference", "debits", "credits", "balance"): (0, -1, 3, 4, 5),
}


def _extract_via_tables(pdf: pdfplumber.PDF) -> RawStatement | None:
    all_rows: list[RawRow] = []
    header_layout: tuple[int, int, int, int, int] | None = None
    remarks_col: int | None = None

    for page_num, page in enumerate(pdf.pages, start=1):
        tables = page.extract_tables({"vertical_strategy": "lines", "horizontal_strategy": "lines"})
        if not tables:
            continue
        table = tables[-1]  # the data table is consistently the last one on the page
        if not table:
            continue

        for row in table:
            if not row or not row[0]:
                continue
            header_key = tuple((c or "").strip().lower() for c in row[: len(row)])
            if header_key[: min(6, len(header_key))] in _KNOWN_HEADERS or row[0].strip() in (
                "Posted Date", "Trans. Date",
            ):
                if header_layout is None:
                    matched = next(
                        (v for k, v in _KNOWN_HEADERS.items() if header_key[: len(k)] == k), None
                    )
                    if matched:
                        header_layout = matched
                        remarks_col = 7 if len(row) > 7 else None
                continue  # header row itself carries no data

            if header_layout is None:
                # First data-looking row seen before we matched a known header —
                # assume Access-style 6-column layout (date, value_date, desc, debit, credit, balance)
                if len(row) == 6:
                    header_layout = (0, 2, 3, 4, 5)
                elif len(row) == 8:
                    header_layout = (0, -1, 3, 4, 5)
                    remarks_col = 7
                else:
                    continue

            di, desci, debi, credi, bali = header_layout
            if di >= len(row):
                continue
            posted = (row[di] or "").strip()
            if not _DATE_TOKEN_RE.match(posted.split("\n")[0].strip()) and not any(
                _parse_date(t) for t in posted.split("\n")
            ):
                continue

            if desci == -1:
                # GTBank-style: description lives in "Reference" + "Remarks"
                ref = (row[2] or "").strip().replace("\n", " ")
                remarks = (row[remarks_col] or "").strip().replace("\n", " ") if remarks_col else ""
                description = f"{ref} {remarks}".strip()
            else:
                description = (row[desci] or "").strip().replace("\n", " ")

            debit = (row[debi] or "-").strip() if debi < len(row) else "-"
            credit = (row[credi] or "-").strip() if credi < len(row) else "-"
            balance = (row[bali] or "0").strip() if bali < len(row) else "0"

            all_rows.append(RawRow(posted, description, debit, credit, balance, page_num))

    if not all_rows:
        return None

    sample_text = "\n".join((p.extract_text() or "") for p in (pdf.pages[:2] + pdf.pages[-1:]))
    return RawStatement(account_hint=_detect_account_hint(sample_text), rows=all_rows, pages_processed=len(pdf.pages))


# ---------------------------------------------------------------------------
# Strategy 2: generic line-reconstruction fallback
# ---------------------------------------------------------------------------

def _group_words_into_lines(page, y_tolerance: float = 3.0) -> list[list[str]]:
    words = page.extract_words()
    words.sort(key=lambda w: (-w["top"], w["x0"]))
    lines: list[list[dict]] = []
    current: list[dict] = []
    current_top: float | None = None
    for w in words:
        if current_top is None or abs(w["top"] - current_top) <= y_tolerance:
            current.append(w)
            current_top = w["top"] if current_top is None else current_top
        else:
            current.sort(key=lambda x: x["x0"])
            lines.append([x["text"] for x in current])
            current = [w]
            current_top = w["top"]
    if current:
        current.sort(key=lambda x: x["x0"])
        lines.append([x["text"] for x in current])
    return lines


def _extract_via_fallback(pdf: pdfplumber.PDF) -> RawStatement:
    all_lines: list[tuple[list[str], int]] = []
    for page_num, page in enumerate(pdf.pages, start=1):
        for line in _group_words_into_lines(page):
            all_lines.append((line, page_num))

    sample_text = "\n".join((p.extract_text() or "") for p in (pdf.pages[:2] + pdf.pages[-1:]))
    account_hint = _detect_account_hint(sample_text)

    rows: list[RawRow] = []
    block: list[list[str]] = []
    block_page = 1

    def flush() -> None:
        nonlocal block
        if not block:
            return
        tokens = [t for line in block for t in line]
        i = 0
        while i < len(tokens) and _parse_date(tokens[i]):
            i += 1
            if i >= 2:
                break
        if i == 0:
            block = []
            return
        j = len(tokens) - 1
        amt_tokens: list[str] = []
        while j >= i and len(amt_tokens) < 3 and _AMOUNT_RE.match(tokens[j]):
            amt_tokens.insert(0, tokens[j])
            j -= 1
        if len(amt_tokens) < 2:
            block = []
            return
        description = " ".join(tokens[i : j + 1]).strip()
        if len(amt_tokens) == 3:
            debit, credit, balance = amt_tokens
        else:
            credit, balance = amt_tokens
            debit = "-"
        if description:
            rows.append(RawRow(tokens[0], description, debit, credit, balance, block_page))
        block = []

    for line, page_num in all_lines:
        starts_with_date = bool(line) and _parse_date(line[0]) is not None
        if starts_with_date and block:
            flush()
        if not block:
            block_page = page_num
        block.append(line)
    flush()

    return RawStatement(account_hint=account_hint, rows=rows, pages_processed=len(pdf.pages), fallback_used=True)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def parse_statement(file: Union[str, Path, BinaryIO]) -> RawStatement:
    """Parse a bank statement PDF into a RawStatement of unnormalized rows.

    Accepts a path or an open binary file-like object (e.g. an uploaded
    FastAPI ``UploadFile.file``).
    """
    try:
        with pdfplumber.open(file) as pdf:
            if not pdf.pages:
                raise StatementParseError("PDF has no pages.")
            result = _extract_via_tables(pdf)
            if result is not None and result.rows:
                return result
            return _extract_via_fallback(pdf)
    except pdfplumber.pdfminer.pdfdocument.PDFPasswordIncorrect as exc:  # type: ignore[attr-defined]
        raise StatementParseError("PDF is password-protected.") from exc
    except Exception as exc:  # noqa: BLE001 — surface as a parse error, not a crash
        raise StatementParseError(f"Could not parse statement: {exc}") from exc

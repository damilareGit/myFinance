"""Stable identity hash for a transaction.

Used for two things that need to agree with each other:
1. Deduplication — the same statement uploaded twice shouldn't double-count.
2. Category overrides — a user correction needs a stable key to attach to,
   one that survives re-parsing the same statement later.

Includes `balance`: statements with many same-day, same-amount rows
(e.g. a string of identical NIP commission fees or VAT charges) are
common, and without balance in the key, two genuinely distinct
transactions collapse into one on insert. Balance is the cheapest
reliable disambiguator available, since it reflects transaction order.
The tradeoff is that if a statement gets re-parsed via a different
extraction path (table vs. fallback) and produces a slightly different
balance for the same row, the row will be treated as new rather than a
duplicate — a minor annoyance (an extra row to clean up), not silent
data loss, so it's the safer failure mode.

Excludes `source_page` (can legitimately shift between parser runs) and
`category_*` (a category correction must not change the hash a correction
is keyed on).
"""
from __future__ import annotations

import hashlib

from .schemas import Transaction


def transaction_hash(t: Transaction) -> str:
    key = "|".join([
        t.date.isoformat(),
        t.description[:40].strip().lower(),
        f"{t.debit:.2f}",
        f"{t.credit:.2f}",
        f"{t.balance:.2f}" if t.balance is not None else "",
        t.account,
    ])
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:24]

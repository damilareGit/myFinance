"use client";

import { useState } from "react";
import { api, ApiError } from "@/lib/api";
import { formatDate, formatMoney } from "@/lib/format";
import type { Category, Transaction } from "@/lib/types";

export function TransactionsTable({
  transactions,
  categories,
  onCorrected,
}: {
  transactions: Transaction[];
  categories: Category[];
  onCorrected: () => void;
}) {
  const [savingHash, setSavingHash] = useState<string | null>(null);
  const [rowError, setRowError] = useState<string | null>(null);

  const sorted = [...transactions].sort((a, b) => b.date.localeCompare(a.date));

  async function handleCategoryChange(txHash: string, categoryId: string) {
    setRowError(null);
    setSavingHash(txHash);
    try {
      await api.patch(`/transactions/${txHash}/category`, { category_id: Number(categoryId) });
      onCorrected();
    } catch (err) {
      setRowError(err instanceof ApiError ? err.message : "Could not update that category.");
    } finally {
      setSavingHash(null);
    }
  }

  if (sorted.length === 0) {
    return <p className="text-sm text-ink-muted">No transactions yet.</p>;
  }

  return (
    <div className="flex flex-col gap-2">
      {rowError && <p className="text-sm text-critical">{rowError}</p>}
      <div className="overflow-x-auto rounded-[18px] border border-border">
        <table className="w-full min-w-[42rem] border-collapse text-sm">
          <thead>
            <tr className="border-b border-border bg-surface-2 text-left text-xs uppercase tracking-wide text-ink-muted">
              <th className="px-4 py-2.5 font-semibold">Date</th>
              <th className="px-4 py-2.5 font-semibold">Description</th>
              <th className="px-4 py-2.5 font-semibold">Account</th>
              <th className="px-4 py-2.5 font-semibold">Category</th>
              <th className="px-4 py-2.5 text-right font-semibold">Amount</th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((t, i) => (
              <tr
                key={t.tx_hash || i}
                className={`border-b border-border last:border-0 ${i % 2 === 1 ? "bg-surface-2/40" : "bg-surface"}`}
              >
                <td className="whitespace-nowrap px-4 py-2.5 tabular-nums text-ink-muted">{formatDate(t.date)}</td>
                <td className="px-4 py-2.5">{t.description}</td>
                <td className="px-4 py-2.5 text-ink-muted">{t.account}</td>
                <td className="px-4 py-2.5">
                  <select
                    value={t.category_id}
                    disabled={savingHash === t.tx_hash}
                    onChange={(e) => handleCategoryChange(t.tx_hash, e.target.value)}
                    className="rounded-lg border border-border bg-bg px-2 py-1 text-xs disabled:opacity-50"
                  >
                    {categories.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.name}
                      </option>
                    ))}
                  </select>
                </td>
                <td
                  className={`whitespace-nowrap px-4 py-2.5 text-right tabular-nums font-semibold ${
                    t.debit > 0 ? "text-critical" : "text-success"
                  }`}
                >
                  {t.debit > 0 ? "-" : "+"}
                  {formatMoney(t.debit > 0 ? t.debit : t.credit, t.currency)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

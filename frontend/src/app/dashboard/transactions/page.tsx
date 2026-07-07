"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useAnalysis } from "@/lib/use-analysis";
import type { Category, StatementAnalysis } from "@/lib/types";
import { UploadStatementForm } from "@/components/dashboard/UploadStatementForm";
import { ManualEntryForm } from "@/components/dashboard/ManualEntryForm";
import { TransactionsTable } from "@/components/dashboard/TransactionsTable";

export default function TransactionsPage() {
  const { analysis, loading, empty, error, refresh } = useAnalysis();
  const [categories, setCategories] = useState<Category[]>([]);

  useEffect(() => {
    api.get<Category[]>("/categories").then(setCategories).catch(() => setCategories([]));
  }, []);

  function handleUpdated(next: StatementAnalysis) {
    // The upload/manual-entry endpoints already return the fresh analysis —
    // avoid an extra round trip by just refreshing from the shared hook,
    // which re-fetches once and keeps state consistent everywhere.
    void next;
    refresh();
  }

  return (
    <>
      <div>
        <p className="text-xs uppercase tracking-wide text-ink-muted">Transactions</p>
        <h1 className="font-display text-2xl font-semibold">Add and review transactions</h1>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="rounded-[18px] border border-border bg-surface p-5">
          <h3 className="mb-3 font-display text-base font-semibold">Upload a statement</h3>
          <UploadStatementForm onUploaded={handleUpdated} />
        </div>
        <div className="rounded-[18px] border border-border bg-surface p-5">
          <h3 className="mb-3 font-display text-base font-semibold">Add a cash purchase</h3>
          <ManualEntryForm categories={categories} onAdded={handleUpdated} />
        </div>
      </div>

      <div>
        <h3 className="mb-3 font-display text-base font-semibold">All transactions</h3>
        {loading && <p className="text-sm text-ink-muted">Loading…</p>}
        {error && <p className="text-sm text-critical">{error}</p>}
        {empty && !loading && <p className="text-sm text-ink-muted">Nothing here yet — add one above.</p>}
        {analysis && !loading && (
          <TransactionsTable transactions={analysis.transactions} categories={categories} onCorrected={refresh} />
        )}
      </div>
    </>
  );
}

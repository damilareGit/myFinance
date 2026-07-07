"use client";

import { useState, type FormEvent } from "react";
import { ApiError } from "@/lib/api";
import type { CategoryKind } from "@/lib/types";

const inputClass =
  "rounded-xl border border-border bg-bg px-3 py-2 text-sm outline-none focus-visible:border-accent";

export function NewCategoryForm({
  onCreate,
}: {
  onCreate: (name: string, kind: CategoryKind) => Promise<void>;
}) {
  const [name, setName] = useState("");
  const [kind, setKind] = useState<CategoryKind>("expense");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!name.trim()) {
      setError("Give the category a name.");
      return;
    }
    setError(null);
    setSubmitting(true);
    try {
      await onCreate(name.trim(), kind);
      setName("");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not create that category.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-wrap items-end gap-3">
      <label className="flex flex-1 min-w-40 flex-col gap-1.5 text-sm">
        <span className="font-medium">Name</span>
        <input
          type="text"
          placeholder="e.g. Pet Care"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className={inputClass}
        />
      </label>
      <label className="flex flex-col gap-1.5 text-sm">
        <span className="font-medium">Type</span>
        <select value={kind} onChange={(e) => setKind(e.target.value as CategoryKind)} className={inputClass}>
          <option value="expense">Expense</option>
          <option value="income">Income</option>
          <option value="transfer">Transfer</option>
        </select>
      </label>
      <button
        type="submit"
        disabled={submitting}
        className="rounded-xl bg-accent px-4 py-2.5 text-sm font-semibold text-accent-ink transition-opacity hover:opacity-90 disabled:opacity-60"
      >
        {submitting ? "Adding…" : "Add category"}
      </button>
      {error && <p className="w-full text-sm text-critical">{error}</p>}
    </form>
  );
}

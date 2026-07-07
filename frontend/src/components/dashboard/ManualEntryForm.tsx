"use client";

import { useState, type FormEvent } from "react";
import { api, ApiError } from "@/lib/api";
import type { Category, StatementAnalysis } from "@/lib/types";

const inputClass =
  "rounded-xl border border-border bg-bg px-3 py-2 text-sm outline-none focus-visible:border-accent";

export function ManualEntryForm({
  categories,
  onAdded,
}: {
  categories: Category[];
  onAdded: (analysis: StatementAnalysis) => void;
}) {
  const [date, setDate] = useState(() => new Date().toISOString().slice(0, 10));
  const [description, setDescription] = useState("");
  const [type, setType] = useState<"expense" | "income">("expense");
  const [amount, setAmount] = useState("");
  const [account, setAccount] = useState("Cash");
  const [currency, setCurrency] = useState("NGN");
  const [categoryId, setCategoryId] = useState<string>("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const parsedAmount = Number(amount);
    if (!description.trim() || !parsedAmount || parsedAmount <= 0) {
      setError("Enter a description and an amount greater than zero.");
      return;
    }
    setError(null);
    setSubmitting(true);
    try {
      const signedAmount = type === "expense" ? parsedAmount : -parsedAmount;
      const analysis = await api.post<StatementAnalysis>("/transactions/manual", {
        date,
        description: description.trim(),
        amount: signedAmount,
        account,
        currency,
        category_id: categoryId ? Number(categoryId) : undefined,
      });
      onAdded(analysis);
      setDescription("");
      setAmount("");
      setCategoryId("");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not add that transaction.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="grid grid-cols-2 gap-3 sm:grid-cols-4">
      <label className="col-span-2 flex flex-col gap-1.5 text-sm sm:col-span-1">
        <span className="font-medium">Date</span>
        <input type="date" required value={date} onChange={(e) => setDate(e.target.value)} className={inputClass} />
      </label>

      <label className="col-span-2 flex flex-col gap-1.5 text-sm">
        <span className="font-medium">Description</span>
        <input
          type="text"
          required
          placeholder="e.g. Market run"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          className={inputClass}
        />
      </label>

      <label className="flex flex-col gap-1.5 text-sm">
        <span className="font-medium">Type</span>
        <select value={type} onChange={(e) => setType(e.target.value as "expense" | "income")} className={inputClass}>
          <option value="expense">Money out</option>
          <option value="income">Money in</option>
        </select>
      </label>

      <label className="flex flex-col gap-1.5 text-sm">
        <span className="font-medium">Amount</span>
        <input
          type="number"
          required
          min="0"
          step="0.01"
          placeholder="0.00"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
          className={inputClass}
        />
      </label>

      <label className="flex flex-col gap-1.5 text-sm">
        <span className="font-medium">Account</span>
        <input type="text" value={account} onChange={(e) => setAccount(e.target.value)} className={inputClass} />
      </label>

      <label className="flex flex-col gap-1.5 text-sm">
        <span className="font-medium">Currency</span>
        <input type="text" value={currency} onChange={(e) => setCurrency(e.target.value.toUpperCase())} className={inputClass} />
      </label>

      <label className="col-span-2 flex flex-col gap-1.5 text-sm sm:col-span-2">
        <span className="font-medium">Category</span>
        <select value={categoryId} onChange={(e) => setCategoryId(e.target.value)} className={inputClass}>
          <option value="">Auto-detect from description</option>
          {categories.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </select>
      </label>

      {error && <p className="col-span-full text-sm text-critical">{error}</p>}

      <button
        type="submit"
        disabled={submitting}
        className="col-span-full self-start rounded-xl bg-accent px-4 py-2.5 text-sm font-semibold text-accent-ink transition-opacity hover:opacity-90 disabled:opacity-60 sm:col-span-1"
      >
        {submitting ? "Adding…" : "Add transaction"}
      </button>
    </form>
  );
}

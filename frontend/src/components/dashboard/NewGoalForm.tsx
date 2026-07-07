"use client";

import { useState, type FormEvent } from "react";
import { api, ApiError } from "@/lib/api";
import type { Goal, GoalKind } from "@/lib/types";

const inputClass =
  "rounded-xl border border-border bg-bg px-3 py-2 text-sm outline-none focus-visible:border-accent";

export function NewGoalForm({ onCreated }: { onCreated: (goal: Goal) => void }) {
  const [name, setName] = useState("");
  const [kind, setKind] = useState<GoalKind>("savings");
  const [targetAmount, setTargetAmount] = useState("");
  const [currentAmount, setCurrentAmount] = useState("0");
  const [targetDate, setTargetDate] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const target = Number(targetAmount);
    if (!name.trim() || !target || target <= 0) {
      setError("Enter a name and a target amount greater than zero.");
      return;
    }
    setError(null);
    setSubmitting(true);
    try {
      const goal = await api.post<Goal>("/goals", {
        name: name.trim(),
        kind,
        target_amount: target,
        current_amount: Number(currentAmount) || 0,
        target_date: targetDate || undefined,
      });
      onCreated(goal);
      setName("");
      setTargetAmount("");
      setCurrentAmount("0");
      setTargetDate("");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not create that goal.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="grid grid-cols-2 gap-3 sm:grid-cols-5">
      <label className="col-span-2 flex flex-col gap-1.5 text-sm sm:col-span-2">
        <span className="font-medium">Name</span>
        <input
          type="text"
          required
          placeholder="e.g. Emergency Fund"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className={inputClass}
        />
      </label>

      <label className="flex flex-col gap-1.5 text-sm">
        <span className="font-medium">Type</span>
        <select value={kind} onChange={(e) => setKind(e.target.value as GoalKind)} className={inputClass}>
          <option value="savings">Savings target</option>
          <option value="debt">Debt payoff</option>
        </select>
      </label>

      <label className="flex flex-col gap-1.5 text-sm">
        <span className="font-medium">Target amount</span>
        <input
          type="number"
          required
          min="0"
          step="0.01"
          placeholder="1,000,000"
          value={targetAmount}
          onChange={(e) => setTargetAmount(e.target.value)}
          className={inputClass}
        />
      </label>

      <label className="flex flex-col gap-1.5 text-sm">
        <span className="font-medium">Already at</span>
        <input
          type="number"
          min="0"
          step="0.01"
          value={currentAmount}
          onChange={(e) => setCurrentAmount(e.target.value)}
          className={inputClass}
        />
      </label>

      <label className="col-span-2 flex flex-col gap-1.5 text-sm sm:col-span-1">
        <span className="font-medium">Target date (optional)</span>
        <input type="date" value={targetDate} onChange={(e) => setTargetDate(e.target.value)} className={inputClass} />
      </label>

      {error && <p className="col-span-full text-sm text-critical">{error}</p>}

      <button
        type="submit"
        disabled={submitting}
        className="col-span-full self-start rounded-xl bg-accent px-4 py-2.5 text-sm font-semibold text-accent-ink transition-opacity hover:opacity-90 disabled:opacity-60 sm:col-span-1"
      >
        {submitting ? "Adding…" : "Add goal"}
      </button>
    </form>
  );
}

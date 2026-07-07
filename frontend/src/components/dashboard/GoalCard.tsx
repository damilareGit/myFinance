"use client";

import { useState } from "react";
import { api, ApiError } from "@/lib/api";
import { formatMoney } from "@/lib/format";
import type { Goal } from "@/lib/types";

export function GoalCard({
  goal,
  editable = false,
  onChanged,
}: {
  goal: Goal;
  editable?: boolean;
  onChanged?: () => void;
}) {
  const [editing, setEditing] = useState(false);
  const [amount, setAmount] = useState(String(goal.current_amount));
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const barClass = goal.progress_pct >= 100 ? "bg-success" : goal.kind === "debt" ? "bg-gold" : "bg-accent";

  async function saveProgress() {
    const value = Number(amount);
    if (Number.isNaN(value) || value < 0) {
      setError("Enter a valid amount.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await api.patch(`/goals/${goal.id}`, { current_amount: value });
      setEditing(false);
      onChanged?.();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not update this goal.");
    } finally {
      setBusy(false);
    }
  }

  async function handleDelete() {
    setBusy(true);
    try {
      await api.delete(`/goals/${goal.id}`);
      onChanged?.();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not delete this goal.");
      setBusy(false);
    }
  }

  return (
    <div className="rounded-[18px] border border-border bg-surface p-4">
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="text-sm font-bold">{goal.name}</p>
          <p className="mt-0.5 text-xs text-ink-muted">
            {goal.kind === "debt" ? "Debt payoff" : "Savings target"}
            {goal.target_date ? ` · due ${new Date(goal.target_date).toLocaleDateString("en-GB", { month: "short", year: "numeric" })}` : ""}
          </p>
        </div>
        {editable && (
          <button
            onClick={handleDelete}
            disabled={busy}
            className="text-xs text-ink-muted hover:text-critical disabled:opacity-50"
            aria-label={`Delete ${goal.name}`}
          >
            Remove
          </button>
        )}
      </div>

      <div className="mt-3 h-2 overflow-hidden rounded-full bg-surface-2">
        <div className={`h-full rounded-full ${barClass}`} style={{ width: `${Math.min(goal.progress_pct, 100)}%` }} />
      </div>

      <div className="mt-1.5 flex justify-between text-xs">
        <span className="tabular-nums text-ink-muted">
          {formatMoney(goal.current_amount, goal.currency)} / {formatMoney(goal.target_amount, goal.currency)}
        </span>
        <span className="font-bold">{goal.progress_pct}%</span>
      </div>

      {goal.pace_message && <p className="mt-2 text-xs text-ink-muted">{goal.pace_message}</p>}

      {editable && (
        <div className="mt-3 border-t border-border pt-3">
          {editing ? (
            <div className="flex items-center gap-2">
              <input
                type="number"
                min="0"
                step="0.01"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                className="w-28 rounded-lg border border-border bg-bg px-2 py-1 text-xs outline-none focus-visible:border-accent"
              />
              <button
                onClick={saveProgress}
                disabled={busy}
                className="rounded-lg bg-accent px-2.5 py-1 text-xs font-semibold text-accent-ink disabled:opacity-60"
              >
                Save
              </button>
              <button onClick={() => setEditing(false)} className="text-xs text-ink-muted">
                Cancel
              </button>
            </div>
          ) : (
            <button
              onClick={() => {
                setAmount(String(goal.current_amount));
                setEditing(true);
              }}
              className="text-xs font-semibold text-accent"
            >
              Update progress
            </button>
          )}
          {error && <p className="mt-1.5 text-xs text-critical">{error}</p>}
        </div>
      )}
    </div>
  );
}

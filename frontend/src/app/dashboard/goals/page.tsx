"use client";

import { useGoals } from "@/lib/use-goals";
import { GoalCard } from "@/components/dashboard/GoalCard";
import { NewGoalForm } from "@/components/dashboard/NewGoalForm";

export default function GoalsPage() {
  const { goals, loading, error, refresh } = useGoals();

  return (
    <>
      <div>
        <p className="text-xs uppercase tracking-wide text-ink-muted">Goals</p>
        <h1 className="font-display text-2xl font-semibold">Savings targets and debt payoff</h1>
      </div>

      <div className="rounded-[18px] border border-border bg-surface p-5">
        <h3 className="mb-3 font-display text-base font-semibold">New goal</h3>
        <NewGoalForm onCreated={refresh} />
      </div>

      <div>
        {loading && <p className="text-sm text-ink-muted">Loading…</p>}
        {error && <p className="text-sm text-critical">{error}</p>}
        {!loading && !error && goals.length === 0 && (
          <p className="text-sm text-ink-muted">No goals yet — add one above to start tracking progress.</p>
        )}
        {goals.length > 0 && (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {goals.map((goal) => (
              <GoalCard key={goal.id} goal={goal} editable onChanged={refresh} />
            ))}
          </div>
        )}
      </div>
    </>
  );
}

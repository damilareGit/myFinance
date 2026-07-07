"use client";

import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { useAnalysis } from "@/lib/use-analysis";
import { useGoals } from "@/lib/use-goals";
import { formatMoney } from "@/lib/format";
import { AdviceCard } from "@/components/dashboard/AdviceCard";
import { StatCard } from "@/components/dashboard/StatCard";
import { CategoryBreakdown } from "@/components/dashboard/CategoryBreakdown";
import { CategorySpendList } from "@/components/dashboard/CategorySpendList";
import { GoalCard } from "@/components/dashboard/GoalCard";
import { EmptyState } from "@/components/dashboard/EmptyState";
import type { StatementAnalysis } from "@/lib/types";

/** No dedicated balance endpoint yet — use the most recent known statement
 * balance if one exists, otherwise fall back to a cumulative estimate from
 * everything recorded (flagged as such in the label). */
function resolveBalance(analysis: StatementAnalysis): { value: number; estimated: boolean } {
  const withBalance = analysis.transactions.filter((t) => t.balance !== null);
  if (withBalance.length > 0) {
    const latest = [...withBalance].sort((a, b) => a.date.localeCompare(b.date)).at(-1)!;
    return { value: latest.balance as number, estimated: false };
  }
  return { value: analysis.total_income - analysis.total_spend, estimated: true };
}

export default function OverviewPage() {
  const { user } = useAuth();
  const { analysis, loading, empty, error, refresh } = useAnalysis();
  const { goals, loading: goalsLoading, refresh: refreshGoals } = useGoals();

  const firstName = user?.display_name?.split(" ")[0] || user?.email;
  const today = new Date().toLocaleDateString("en-GB", {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
  });

  return (
    <>
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <div>
          <p className="text-xs uppercase tracking-wide text-ink-muted">Overview</p>
          <h1 className="font-display text-2xl font-semibold">Good day, {firstName}</h1>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-sm text-ink-muted">{today}</span>
          <button
            onClick={refresh}
            className="rounded-lg border border-border px-3 py-1.5 text-xs font-semibold text-ink-muted hover:text-ink"
          >
            Refresh
          </button>
        </div>
      </div>

      {loading && <p className="text-sm text-ink-muted">Loading your dashboard…</p>}
      {error && <p className="text-sm text-critical">{error}</p>}
      {empty && !loading && <EmptyState />}

      {analysis && !loading && (
        <>
          <AdviceCard insight={analysis.insights[0] ?? null} />

          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            {(() => {
              const balance = resolveBalance(analysis);
              return (
                <StatCard
                  label={balance.estimated ? "Balance (estimated)" : "Total balance"}
                  value={formatMoney(balance.value, analysis.primary_currency)}
                />
              );
            })()}
            <StatCard
              label="Income"
              value={formatMoney(analysis.total_income, analysis.primary_currency)}
              tone="up"
            />
            <StatCard
              label="Expenses"
              value={formatMoney(analysis.total_spend, analysis.primary_currency)}
            />
            <StatCard
              label="Savings rate"
              value={`${analysis.overall_savings_rate_pct}%`}
              tone={analysis.overall_savings_rate_pct >= 15 ? "up" : "down"}
            />
          </div>

          <div className="grid gap-4 lg:grid-cols-[1.05fr_1.3fr]">
            <div className="rounded-[18px] border border-border bg-surface p-5">
              <h3 className="mb-4 font-display text-base font-semibold">Spending breakdown</h3>
              <CategoryBreakdown categoryTotals={analysis.category_totals} />
            </div>
            <div className="rounded-[18px] border border-border bg-surface p-5">
              <h3 className="mb-4 font-display text-base font-semibold">Top categories</h3>
              <CategorySpendList categoryTotals={analysis.category_totals} currency={analysis.primary_currency} />
            </div>
          </div>
        </>
      )}

      {/* Goals are independent of transaction data, so this renders even
          before the first statement/manual entry — a new user should be
          able to set a target on day one. */}
      <div>
        <div className="mb-3 flex items-baseline justify-between">
          <h3 className="font-display text-base font-semibold">Goals</h3>
          <Link href="/dashboard/goals" className="text-xs font-semibold text-accent">
            Manage goals
          </Link>
        </div>
        {!goalsLoading && goals.length === 0 && (
          <div className="rounded-[18px] border border-dashed border-border bg-surface p-6 text-center">
            <p className="text-sm text-ink-muted">
              No goals yet.{" "}
              <Link href="/dashboard/goals" className="font-semibold text-accent">
                Set a savings target or debt payoff goal
              </Link>
              .
            </p>
          </div>
        )}
        {goals.length > 0 && (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {goals.slice(0, 3).map((goal) => (
              <GoalCard key={goal.id} goal={goal} onChanged={refreshGoals} />
            ))}
          </div>
        )}
      </div>
    </>
  );
}

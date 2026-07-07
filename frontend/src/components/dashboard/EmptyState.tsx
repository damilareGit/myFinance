import Link from "next/link";

export function EmptyState() {
  return (
    <div className="flex flex-col items-center gap-3 rounded-[18px] border border-dashed border-border bg-surface px-6 py-14 text-center">
      <p className="font-display text-lg font-semibold">No transactions yet</p>
      <p className="max-w-sm text-sm text-ink-muted">
        Upload a bank statement or add a cash purchase to see your spending broken down and get your
        first piece of advice.
      </p>
      <Link
        href="/dashboard/transactions"
        className="mt-2 rounded-xl bg-accent px-4 py-2.5 text-sm font-semibold text-accent-ink transition-opacity hover:opacity-90"
      >
        Add your first transaction
      </Link>
    </div>
  );
}

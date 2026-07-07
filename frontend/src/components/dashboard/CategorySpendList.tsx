import type { CategoryTotal } from "@/lib/types";
import { formatMoney } from "@/lib/format";

export function CategorySpendList({
  categoryTotals,
  currency,
}: {
  categoryTotals: CategoryTotal[];
  currency: string;
}) {
  const expenses = categoryTotals
    .filter((c) => c.category_kind === "expense" && c.debit > 0)
    .sort((a, b) => b.debit - a.debit)
    .slice(0, 6);

  if (expenses.length === 0) {
    return <p className="text-sm text-ink-muted">No spending recorded yet.</p>;
  }

  const max = expenses[0].debit;

  return (
    <div className="flex flex-col gap-3.5">
      {expenses.map((c) => (
        <div key={c.category_id}>
          <div className="mb-1.5 flex justify-between text-sm">
            <span>{c.category_name}</span>
            <span className="tabular-nums text-ink-muted">{formatMoney(c.debit, currency)}</span>
          </div>
          <div className="h-2 overflow-hidden rounded-full bg-surface-2">
            <div className="h-full rounded-full bg-accent" style={{ width: `${(c.debit / max) * 100}%` }} />
          </div>
        </div>
      ))}
    </div>
  );
}

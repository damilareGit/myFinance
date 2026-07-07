import type { CategoryTotal } from "@/lib/types";

const SLICE_COLORS = ["var(--accent)", "var(--gold)", "var(--success)", "#8A6E4B", "var(--ink-muted)"];
const MAX_SLICES = 4; // top 4 categories + an "Other" bucket

export function CategoryBreakdown({ categoryTotals }: { categoryTotals: CategoryTotal[] }) {
  const expenses = categoryTotals
    .filter((c) => c.category_kind === "expense" && c.debit > 0)
    .sort((a, b) => b.debit - a.debit);

  const total = expenses.reduce((sum, c) => sum + c.debit, 0);

  if (total === 0) {
    return <p className="text-sm text-ink-muted">No spending recorded yet.</p>;
  }

  const top = expenses.slice(0, MAX_SLICES);
  const rest = expenses.slice(MAX_SLICES);
  const restTotal = rest.reduce((sum, c) => sum + c.debit, 0);

  const slices = [
    ...top.map((c) => ({ name: c.category_name, amount: c.debit })),
    ...(restTotal > 0 ? [{ name: "Other", amount: restTotal }] : []),
  ];

  let cursor = 0;
  const gradientParts = slices.map((slice, i) => {
    const start = cursor;
    const pct = (slice.amount / total) * 100;
    cursor += pct;
    return `${SLICE_COLORS[i % SLICE_COLORS.length]} ${start}% ${cursor}%`;
  });

  return (
    <div className="flex flex-wrap items-center gap-6">
      <div
        className="relative shrink-0 rounded-full"
        style={{ background: `conic-gradient(${gradientParts.join(", ")})`, width: "9.5rem", height: "9.5rem" }}
      >
        <div className="absolute inset-[19%] rounded-full bg-surface" />
      </div>
      <ul className="flex min-w-40 flex-1 flex-col gap-2 text-sm">
        {slices.map((slice, i) => (
          <li key={slice.name} className="flex items-center justify-between gap-3">
            <span className="flex items-center gap-2">
              <span
                className="inline-block h-2.5 w-2.5 rounded-sm"
                style={{ background: SLICE_COLORS[i % SLICE_COLORS.length] }}
              />
              {slice.name}
            </span>
            <span className="tabular-nums text-ink-muted">{((slice.amount / total) * 100).toFixed(0)}%</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

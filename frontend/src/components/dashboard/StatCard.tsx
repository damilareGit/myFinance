export function StatCard({
  label,
  value,
  delta,
  tone = "neutral",
}: {
  label: string;
  value: string;
  delta?: string;
  tone?: "up" | "down" | "neutral";
}) {
  return (
    <div className="rounded-[18px] border border-border bg-surface p-4">
      <p className="text-xs text-ink-muted">{label}</p>
      <p className="mt-1.5 font-display text-2xl tabular-nums">{value}</p>
      {delta && (
        <p
          className={`mt-1 text-xs font-bold ${
            tone === "up" ? "text-success" : tone === "down" ? "text-critical" : "text-ink-muted"
          }`}
        >
          {tone === "up" ? "▲ " : tone === "down" ? "▼ " : ""}
          {delta}
        </p>
      )}
    </div>
  );
}

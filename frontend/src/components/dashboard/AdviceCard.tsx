import type { Insight } from "@/lib/types";

const CHIP_LABEL: Record<Insight["tone"], string> = {
  good: "On track",
  warn: "Worth a look",
  neutral: "Heads up",
};

export function AdviceCard({ insight }: { insight: Insight | null }) {
  if (!insight) return null;

  return (
    <div className="flex items-start gap-4 rounded-[18px] border border-accent/30 bg-accent/10 p-5">
      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-accent font-display text-base font-bold text-accent-ink">
        F
      </div>
      <div className="flex flex-col gap-1.5">
        <span className="w-fit rounded-full bg-gold/25 px-2.5 py-1 text-[0.68rem] font-bold uppercase tracking-wide text-ink">
          {CHIP_LABEL[insight.tone]}
        </span>
        <p className="font-display text-base leading-relaxed">{insight.message}</p>
      </div>
    </div>
  );
}

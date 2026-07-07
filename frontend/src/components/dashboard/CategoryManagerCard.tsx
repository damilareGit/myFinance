"use client";

import { useState } from "react";
import { ApiError } from "@/lib/api";
import type { Category, CategoryRule } from "@/lib/types";

export function CategoryManagerCard({
  category,
  rules,
  onAddRule,
  onDeleteRule,
  onDeleteCategory,
}: {
  category: Category;
  rules: CategoryRule[];
  onAddRule: (categoryId: number, keyword: string) => Promise<void>;
  onDeleteRule: (ruleId: number) => Promise<void>;
  onDeleteCategory: (categoryId: number) => Promise<void>;
}) {
  const [keyword, setKeyword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleAddRule() {
    if (!keyword.trim()) return;
    setBusy(true);
    setError(null);
    try {
      await onAddRule(category.id, keyword.trim());
      setKeyword("");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not add that keyword.");
    } finally {
      setBusy(false);
    }
  }

  async function handleDeleteRule(ruleId: number) {
    setBusy(true);
    setError(null);
    try {
      await onDeleteRule(ruleId);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not remove that keyword.");
    } finally {
      setBusy(false);
    }
  }

  async function handleDeleteCategory() {
    setBusy(true);
    setError(null);
    try {
      await onDeleteCategory(category.id);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not delete this category.");
      setBusy(false);
    }
  }

  return (
    <div className="rounded-[18px] border border-border bg-surface p-4">
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2">
          <p className="text-sm font-bold">{category.name}</p>
          <span className="rounded-full bg-surface-2 px-1.5 py-0.5 text-[0.65rem] font-bold uppercase tracking-wide text-ink-muted">
            {category.is_custom ? "Custom" : "Default"}
          </span>
        </div>
        {category.is_custom && (
          <button
            onClick={handleDeleteCategory}
            disabled={busy}
            className="text-xs text-ink-muted hover:text-critical disabled:opacity-50"
          >
            Delete
          </button>
        )}
      </div>

      <div className="mt-3 flex flex-wrap gap-1.5">
        {rules.length === 0 && <p className="text-xs text-ink-muted">No keywords yet — matches nothing automatically.</p>}
        {rules.map((rule) => (
          <span
            key={rule.id}
            className="flex items-center gap-1 rounded-full border border-border bg-bg px-2 py-1 text-xs"
          >
            {rule.keyword}
            {rule.is_custom && (
              <button
                onClick={() => handleDeleteRule(rule.id)}
                disabled={busy}
                aria-label={`Remove keyword ${rule.keyword}`}
                className="text-ink-muted hover:text-critical disabled:opacity-50"
              >
                ×
              </button>
            )}
          </span>
        ))}
      </div>

      <div className="mt-3 flex items-center gap-2">
        <input
          type="text"
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              e.preventDefault();
              handleAddRule();
            }
          }}
          placeholder="Add a keyword…"
          className="min-w-0 flex-1 rounded-lg border border-border bg-bg px-2 py-1 text-xs outline-none focus-visible:border-accent"
        />
        <button
          onClick={handleAddRule}
          disabled={busy || !keyword.trim()}
          className="rounded-lg bg-accent px-2.5 py-1 text-xs font-semibold text-accent-ink disabled:opacity-60"
        >
          Add
        </button>
      </div>
      {error && <p className="mt-1.5 text-xs text-critical">{error}</p>}
    </div>
  );
}

"use client";

import { useCategories } from "@/lib/use-categories";
import { NewCategoryForm } from "@/components/dashboard/NewCategoryForm";
import { CategoryManagerCard } from "@/components/dashboard/CategoryManagerCard";
import type { CategoryKind } from "@/lib/types";

const KIND_LABELS: Record<CategoryKind, string> = {
  income: "Income",
  expense: "Expenses",
  transfer: "Transfers",
};

const KIND_ORDER: CategoryKind[] = ["income", "expense", "transfer"];

export default function CategoriesPage() {
  const { categories, rules, loading, error, createCategory, deleteCategory, addRule, deleteRule } = useCategories();

  return (
    <>
      <div>
        <p className="text-xs uppercase tracking-wide text-ink-muted">Categories</p>
        <h1 className="font-display text-2xl font-semibold">Categories and keyword rules</h1>
        <p className="mt-1 max-w-2xl text-sm text-ink-muted">
          Every transaction is auto-categorized by matching its description against these keywords.
          Default categories are shared; anything you add here — new categories or keywords — only
          applies to your own account.
        </p>
      </div>

      <div className="rounded-[18px] border border-border bg-surface p-5">
        <h3 className="mb-3 font-display text-base font-semibold">New category</h3>
        <NewCategoryForm onCreate={createCategory} />
      </div>

      {loading && <p className="text-sm text-ink-muted">Loading…</p>}
      {error && <p className="text-sm text-critical">{error}</p>}

      {!loading &&
        !error &&
        KIND_ORDER.map((kind) => {
          const inGroup = categories.filter((c) => c.kind === kind);
          if (inGroup.length === 0) return null;
          return (
            <div key={kind}>
              <h3 className="mb-3 font-display text-base font-semibold">{KIND_LABELS[kind]}</h3>
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {inGroup.map((category) => (
                  <CategoryManagerCard
                    key={category.id}
                    category={category}
                    rules={rules.filter((r) => r.category_id === category.id)}
                    onAddRule={addRule}
                    onDeleteRule={deleteRule}
                    onDeleteCategory={deleteCategory}
                  />
                ))}
              </div>
            </div>
          );
        })}
    </>
  );
}

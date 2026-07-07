"use client";

import { useCallback, useEffect, useState } from "react";
import { api, ApiError } from "./api";
import type { Category, CategoryKind, CategoryRule } from "./types";

export function useCategories() {
  const [categories, setCategories] = useState<Category[]>([]);
  const [rules, setRules] = useState<CategoryRule[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [cats, ruleList] = await Promise.all([
        api.get<Category[]>("/categories"),
        api.get<CategoryRule[]>("/categories/rules"),
      ]);
      setCategories(cats);
      setRules(ruleList);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not load categories.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  async function createCategory(name: string, kind: CategoryKind) {
    await api.post<Category>("/categories", { name, kind });
    await refresh();
  }

  async function deleteCategory(id: number) {
    await api.delete(`/categories/${id}`);
    await refresh();
  }

  async function addRule(categoryId: number, keyword: string) {
    await api.post(`/categories/${categoryId}/rules`, { keyword });
    await refresh();
  }

  async function deleteRule(ruleId: number) {
    await api.delete(`/categories/rules/${ruleId}`);
    await refresh();
  }

  return { categories, rules, loading, error, refresh, createCategory, deleteCategory, addRule, deleteRule };
}

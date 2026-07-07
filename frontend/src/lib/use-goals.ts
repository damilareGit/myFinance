"use client";

import { useCallback, useEffect, useState } from "react";
import { api, ApiError } from "./api";
import type { Goal } from "./types";

export function useGoals() {
  const [goals, setGoals] = useState<Goal[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.get<Goal[]>("/goals");
      setGoals(data);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not load your goals.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { goals, loading, error, refresh };
}

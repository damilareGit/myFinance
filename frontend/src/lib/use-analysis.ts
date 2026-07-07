"use client";

import { useCallback, useEffect, useState } from "react";
import { api, ApiError } from "./api";
import type { StatementAnalysis } from "./types";

interface AnalysisState {
  analysis: StatementAnalysis | null;
  loading: boolean;
  empty: boolean;
  error: string | null;
  refresh: () => Promise<void>;
}

export function useAnalysis(): AnalysisState {
  const [analysis, setAnalysis] = useState<StatementAnalysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [empty, setEmpty] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.get<StatementAnalysis>("/transactions/analysis");
      setAnalysis(data);
      setEmpty(false);
    } catch (err) {
      if (err instanceof ApiError && err.status === 404) {
        setAnalysis(null);
        setEmpty(true);
      } else {
        setError(err instanceof ApiError ? err.message : "Could not load your data.");
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { analysis, loading, empty, error, refresh };
}

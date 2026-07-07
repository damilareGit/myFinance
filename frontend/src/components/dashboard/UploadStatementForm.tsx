"use client";

import { useRef, useState, type FormEvent } from "react";
import { api, ApiError } from "@/lib/api";
import type { StatementAnalysis } from "@/lib/types";

export function UploadStatementForm({ onUploaded }: { onUploaded: (analysis: StatementAnalysis) => void }) {
  const fileInput = useRef<HTMLInputElement>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fileName, setFileName] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const file = fileInput.current?.files?.[0];
    if (!file) {
      setError("Choose a PDF statement first.");
      return;
    }
    setError(null);
    setSubmitting(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const analysis = await api.upload<StatementAnalysis>("/transactions/upload", formData);
      onUploaded(analysis);
      if (fileInput.current) fileInput.current.value = "";
      setFileName(null);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not parse that statement.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-3">
      <label
        htmlFor="statement-file"
        className="flex cursor-pointer flex-col items-center gap-1.5 rounded-xl border border-dashed border-border bg-bg px-4 py-6 text-center text-sm text-ink-muted hover:border-accent hover:text-ink"
      >
        <span className="font-semibold">{fileName ?? "Choose a PDF bank statement"}</span>
        <span className="text-xs">Access Bank and GTBank layouts are best supported today</span>
        <input
          id="statement-file"
          ref={fileInput}
          type="file"
          accept="application/pdf"
          className="hidden"
          onChange={(e) => setFileName(e.target.files?.[0]?.name ?? null)}
        />
      </label>

      {error && <p className="text-sm text-critical">{error}</p>}

      <button
        type="submit"
        disabled={submitting}
        className="self-start rounded-xl bg-accent px-4 py-2.5 text-sm font-semibold text-accent-ink transition-opacity hover:opacity-90 disabled:opacity-60"
      >
        {submitting ? "Uploading…" : "Upload statement"}
      </button>
    </form>
  );
}

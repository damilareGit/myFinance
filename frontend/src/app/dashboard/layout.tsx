"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { Sidebar } from "@/components/Sidebar";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) {
      router.replace("/login");
    }
  }, [user, loading, router]);

  if (loading || !user) {
    return (
      <div className="flex min-h-screen items-center justify-center text-sm text-ink-muted">
        Loading FinAdvisor…
      </div>
    );
  }

  return (
    <div className="mx-auto flex min-h-screen max-w-[76rem] rounded-none border-border bg-bg md:my-6 md:overflow-hidden md:rounded-[22px] md:border">
      <Sidebar />
      <main className="flex flex-1 flex-col gap-6 px-5 py-7 md:px-8">{children}</main>
    </div>
  );
}

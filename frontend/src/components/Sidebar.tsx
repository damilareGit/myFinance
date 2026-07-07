"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Overview" },
  { href: "/dashboard/transactions", label: "Transactions" },
  { href: "/dashboard/goals", label: "Goals" },
  { href: "/dashboard/categories", label: "Categories" },
];

export function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const router = useRouter();

  async function handleLogout() {
    await logout();
    router.replace("/login");
  }

  return (
    <aside className="hidden w-60 shrink-0 flex-col gap-8 border-r border-border bg-surface px-5 py-7 md:flex">
      <p className="font-display text-xl font-semibold">
        Fin<span className="text-accent">Advisor</span>
      </p>

      <nav className="flex flex-col gap-1">
        {NAV_ITEMS.map((item) => {
          const active = item.href === pathname;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`rounded-[10px] px-3 py-2 text-sm font-semibold transition-colors ${
                active ? "bg-accent text-accent-ink" : "text-ink-muted hover:bg-surface-2 hover:text-ink"
              }`}
            >
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="mt-auto flex flex-col gap-2 border-t border-border pt-4 text-sm">
        <p className="font-semibold">{user?.display_name || user?.email}</p>
        <button
          onClick={handleLogout}
          className="self-start text-ink-muted underline decoration-dotted underline-offset-4 hover:text-accent"
        >
          Log out
        </button>
      </div>
    </aside>
  );
}

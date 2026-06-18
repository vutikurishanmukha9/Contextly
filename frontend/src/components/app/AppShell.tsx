import { Link, useRouterState } from "@tanstack/react-router";
import { Logo } from "@/components/site/Logo";
import { LayoutDashboard, Search, Bell } from "lucide-react";
import type { ReactNode } from "react";

const nav = [{ to: "/", label: "Dashboard", icon: LayoutDashboard }];

export function AppShell({
  title,
  subtitle,
  actions,
  children,
  user = { name: "User", plan: "Free Tier" },
}: {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
  children: ReactNode;
  user?: { name: string; plan: string };
}) {
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  return (
    <div className="flex min-h-screen w-full bg-background">
      <aside className="hidden w-[248px] shrink-0 flex-col border-r border-border bg-surface md:flex">
        <div className="flex h-16 items-center px-5 border-b border-border">
          <Logo />
        </div>
        <nav className="flex-1 px-3 py-4">
          <div className="px-2 pb-2 text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
            Workspace
          </div>
          <ul className="space-y-0.5">
            {nav.map((item) => {
              const active = pathname === item.to;
              const Icon = item.icon;
              return (
                <li key={item.to}>
                  <Link
                    to={item.to}
                    className={`group flex items-center gap-2.5 rounded-md px-2.5 py-2 text-[13.5px] transition-colors ${
                      active
                        ? "bg-muted text-foreground"
                        : "text-muted-foreground hover:bg-muted/60 hover:text-foreground"
                    }`}
                  >
                    <Icon className={`h-4 w-4 ${active ? "text-primary" : ""}`} />
                    {item.label}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>
        <div className="border-t border-border p-3">
          <div className="flex items-center gap-2.5 rounded-md p-2">
            <div className="h-8 w-8 rounded-full bg-gradient-to-br from-primary to-[#8B95E5]" />
            <div className="min-w-0">
              <div className="truncate text-[13px] font-medium">{user.name}</div>
              <div className="truncate text-[11.5px] text-muted-foreground">{user.plan}</div>
            </div>
          </div>
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-30 flex h-16 items-center gap-3 border-b border-border bg-background/80 px-6 backdrop-blur">
          <div className="flex flex-1 items-center gap-3">
            <div className="hidden items-center gap-2 rounded-md border border-border bg-surface px-3 py-1.5 md:flex md:w-[320px]">
              <Search className="h-3.5 w-3.5 text-muted-foreground" />
              <input
                className="flex-1 bg-transparent text-[13px] outline-none placeholder:text-muted-foreground"
                placeholder="Search context, memory, packs..."
              />
              <kbd className="text-mono text-[10.5px] text-muted-foreground">Ctrl K</kbd>
            </div>
          </div>
          <button className="rounded-md p-2 text-muted-foreground hover:bg-muted hover:text-foreground">
            <Bell className="h-4 w-4" />
          </button>
        </header>

        <div className="border-b border-border bg-background px-8 py-7">
          <div className="flex flex-wrap items-end justify-between gap-4">
            <div>
              <h1 className="text-display text-[28px] font-semibold">{title}</h1>
              {subtitle && <p className="mt-1.5 text-[14px] text-muted-foreground">{subtitle}</p>}
            </div>
            {actions && <div className="flex items-center gap-2">{actions}</div>}
          </div>
        </div>

        <main className="flex-1 px-8 py-8">{children}</main>
      </div>
    </div>
  );
}

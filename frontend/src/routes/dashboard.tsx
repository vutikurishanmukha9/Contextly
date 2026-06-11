import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/app/AppShell";
import { ArrowUpRight, Sparkles, TrendingUp, Zap } from "lucide-react";

export const Route = createFileRoute("/dashboard")({
  head: () => ({ meta: [{ title: "Dashboard — Context-Ly" }] }),
  component: Dashboard,
});

function Dashboard() {
  return (
    <AppShell
      title="Welcome back, Ada"
      subtitle="Here's what's happening across your context workspace today."
      actions={
        <>
          <button className="rounded-pill border border-border bg-surface px-4 py-2 text-[13px] font-medium hover:bg-muted">Import</button>
          <button className="rounded-pill bg-foreground px-4 py-2 text-[13px] font-medium text-background hover:opacity-90">New context pack</button>
        </>
      }
    >
      <div className="grid gap-5 md:grid-cols-3">
        <ScoreCard />
        <Stat label="Tokens saved this week" value="24,512" delta="+18.2%" icon={Zap} tone="bg-mint" />
        <Stat label="Active projects" value="12" delta="+2 new" icon={Sparkles} tone="bg-lavender" />
      </div>

      <div className="mt-6 grid gap-5 lg:grid-cols-3">
        <div className="surface-card p-6 lg:col-span-2">
          <Header title="Recent context packs" sub="Last edited across all projects" />
          <div className="mt-5 divide-y divide-border">
            {[
              ["Onboarding · Customer support", "Pack · 8 blocks · 2,140 tokens", 94, "2h ago"],
              ["Q4 Launch · Marketing brief", "Pack · 12 blocks · 3,820 tokens", 88, "Yesterday"],
              ["Codebase · Auth refactor", "Pack · 6 blocks · 1,420 tokens", 96, "2d ago"],
              ["Sales · Enterprise demo script", "Pack · 9 blocks · 2,640 tokens", 82, "3d ago"],
            ].map(([t, m, s, when]) => (
              <div key={t as string} className="flex items-center justify-between gap-4 py-4">
                <div className="min-w-0">
                  <div className="truncate text-[14px] font-medium">{t}</div>
                  <div className="truncate text-[12.5px] text-muted-foreground">{m}</div>
                </div>
                <div className="flex items-center gap-5">
                  <div className="hidden items-center gap-2 md:flex">
                    <div className="h-1.5 w-24 overflow-hidden rounded-pill bg-muted">
                      <div className="h-full score-gradient" style={{ width: `${s as number}%` }} />
                    </div>
                    <span className="text-mono text-[12px] w-7 text-right">{s as number}</span>
                  </div>
                  <span className="hidden text-[12px] text-muted-foreground md:inline">{when}</span>
                  <button className="rounded-md p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground">
                    <ArrowUpRight className="h-4 w-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
        <div className="surface-card p-6">
          <Header title="AI model activity" sub="Last 7 days" />
          <div className="mt-5 space-y-4">
            {[
              ["GPT-4o", 64, "12,420 tok"],
              ["Claude Sonnet", 48, "9,180 tok"],
              ["Mistral Large", 28, "5,640 tok"],
              ["Llama 3.1", 18, "3,200 tok"],
            ].map(([m, w, t]) => (
              <div key={m as string}>
                <div className="flex items-baseline justify-between">
                  <span className="text-[13px] font-medium">{m}</span>
                  <span className="text-mono text-[12px] text-muted-foreground">{t}</span>
                </div>
                <div className="mt-1.5 h-1.5 overflow-hidden rounded-pill bg-muted">
                  <div className="h-full rounded-pill bg-foreground/80" style={{ width: `${w as number}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="mt-6 surface-card p-6">
        <Header title="Usage trends" sub="Tokens processed vs. tokens sent to models" />
        <Sparkline />
      </div>
    </AppShell>
  );
}

function Header({ title, sub }: { title: string; sub: string }) {
  return (
    <div className="flex items-end justify-between">
      <div>
        <div className="text-display text-[16px] font-semibold">{title}</div>
        <div className="text-[12.5px] text-muted-foreground">{sub}</div>
      </div>
    </div>
  );
}

function Stat({ label, value, delta, icon: Icon, tone }: any) {
  return (
    <div className="surface-card p-6">
      <div className="flex items-center justify-between">
        <span className="text-[13px] text-muted-foreground">{label}</span>
        <span className={`inline-flex h-8 w-8 items-center justify-center rounded-md ${tone}`}>
          <Icon className="h-4 w-4 text-foreground/80" />
        </span>
      </div>
      <div className="text-display mt-4 text-[36px] font-semibold">{value}</div>
      <div className="mt-1 inline-flex items-center gap-1 text-[12.5px] text-success">
        <TrendingUp className="h-3.5 w-3.5" /> {delta}
      </div>
    </div>
  );
}

function ScoreCard() {
  return (
    <div className="surface-card p-6">
      <div className="flex items-center justify-between">
        <span className="text-[13px] text-muted-foreground">Workspace context score</span>
        <span className="rounded-pill bg-mint px-2 py-0.5 text-[11px] font-medium">Excellent</span>
      </div>
      <div className="text-display mt-4 text-[36px] font-semibold">92</div>
      <div className="mt-3 h-2 overflow-hidden rounded-pill bg-muted">
        <div className="h-full score-gradient" style={{ width: "92%" }} />
      </div>
      <div className="mt-4 grid grid-cols-4 gap-3 text-center">
        {[["Rlv","96"],["Cmp","89"],["Red","88"],["Clr","94"]].map(([k,v]) => (
          <div key={k} className="rounded-md bg-muted/60 py-2">
            <div className="text-mono text-[11px] text-muted-foreground">{k}</div>
            <div className="text-[13px] font-semibold">{v}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

function Sparkline() {
  const data = [22, 30, 28, 44, 38, 60, 52, 70, 64, 82, 76, 92];
  const data2 = [12, 16, 14, 22, 18, 28, 22, 30, 24, 32, 28, 34];
  const max = 100;
  const w = 100, h = 100;
  const path = (arr: number[]) =>
    arr.map((v, i) => `${(i * w) / (arr.length - 1)},${h - (v / max) * h}`).join(" ");
  return (
    <div className="mt-6">
      <svg viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none" className="h-56 w-full">
        <polyline fill="none" stroke="rgba(17,17,17,0.15)" strokeWidth="0.8" points={path(data)} />
        <polyline fill="none" stroke="var(--primary)" strokeWidth="1.4" points={path(data2)} />
      </svg>
      <div className="mt-3 flex gap-5 text-[12px] text-muted-foreground">
        <span className="inline-flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-foreground/30" /> Processed</span>
        <span className="inline-flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-primary" /> Sent to model</span>
      </div>
    </div>
  );
}

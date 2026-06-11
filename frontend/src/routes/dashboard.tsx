import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/app/AppShell";
import { ArrowUpRight, Sparkles, TrendingUp, Zap } from "lucide-react";

export const Route = createFileRoute("/dashboard")({
  head: () => ({ meta: [{ title: "CLI Reference — Context-Ly" }] }),
  component: Dashboard,
});

function Dashboard() {
  return (
    <AppShell
      title="CLI Command Center"
      subtitle="The ultimate reference for Context-Ly terminal operations."
      actions={
        <>
          <button className="rounded-pill border border-border bg-surface px-4 py-2 text-[13px] font-medium hover:bg-muted">Import</button>
          <button className="rounded-pill bg-foreground px-4 py-2 text-[13px] font-medium text-background hover:opacity-90">New context pack</button>
        </>
      }
    >
      <div className="grid gap-5 md:grid-cols-3">
        <ScoreCard />
        <Stat label="Total CLI Commands" value="7" delta="Fully stable" icon={Zap} tone="bg-mint" />
        <Stat label="Supported Frameworks" value="All" delta="Language agnostic" icon={Sparkles} tone="bg-lavender" />
      </div>

      <div className="mt-6 grid gap-5 lg:grid-cols-3">
        <div className="surface-card p-6 lg:col-span-2">
          <Header title="Command Reference" sub="The 7 pillars of Context-Ly" />
          <div className="mt-5 divide-y divide-border">
            {[
              ["contextly init", "Initializes Context-as-Code in the current directory.", "Core", "Stable"],
              ["contextly analyze", "Builds the master PROJECT_CONTEXT.md architecture map.", "Intelligence", "Stable"],
              ["contextly discover", "Statically analyzes heuristics to find unwritten rules.", "Scanner", "Stable"],
              ["contextly learn --auto", "Interactive gatekeeper to permanently save rules to memory.", "Memory", "Stable"],
              ["contextly pack <dir>", "Bundles a directory into a highly compressed LLM context pack.", "Packager", "Stable"],
              ["contextly export", "Fuses intelligence and context packs straight to your clipboard.", "Exporter", "Stable"],
              ["contextly memory", "Inspects the YAML rules saved in your project memory.", "Memory", "Stable"],
            ].map(([cmd, desc, category, status]) => (
              <div key={cmd as string} className="flex items-center justify-between gap-4 py-4">
                <div className="min-w-0">
                  <div className="truncate text-[14px] font-mono font-medium text-primary">{cmd}</div>
                  <div className="truncate text-[12.5px] text-muted-foreground">{desc}</div>
                </div>
                <div className="flex items-center gap-5">
                  <div className="hidden items-center gap-2 md:flex">
                    <span className="rounded-pill border border-border bg-muted/50 px-2 py-0.5 text-[11px] text-foreground/80">{category}</span>
                  </div>
                  <span className="hidden text-[12px] text-success md:inline">{status}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
        <div className="surface-card p-6">
          <Header title="Best Practices" sub="Getting the most out of LLMs" />
          <div className="mt-5 space-y-4">
            {[
              ["Never guess the stack", "Always run analyze first"],
              ["Don't trust the robot", "Use learn --auto to confirm"],
              ["Avoid token bloat", "Use pack to select folders"],
              ["Trust requires visibility", "Use memory to inspect rules"],
            ].map(([title, tip]) => (
              <div key={title as string}>
                <div className="flex flex-col">
                  <span className="text-[13px] font-medium">{title}</span>
                  <span className="text-[12px] text-muted-foreground">{tip}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
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
        <span className="text-[13px] text-muted-foreground">Context Output Formatting</span>
        <span className="rounded-pill bg-mint px-2 py-0.5 text-[11px] font-medium">Perfect</span>
      </div>
      <div className="text-display mt-4 text-[36px] font-semibold">XML</div>
      <div className="mt-3 h-2 overflow-hidden rounded-pill bg-muted">
        <div className="h-full score-gradient" style={{ width: "100%" }} />
      </div>
      <div className="mt-4 grid grid-cols-4 gap-3 text-center">
        {[["Code","✓"],["Maps","✓"],["Rules","✓"],["Tags","✓"]].map(([k,v]) => (
          <div key={k} className="rounded-md bg-muted/60 py-2">
            <div className="text-mono text-[11px] text-muted-foreground">{k}</div>
            <div className="text-[13px] font-semibold">{v}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

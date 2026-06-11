import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/app/AppShell";
import { ArrowRight, Sparkles } from "lucide-react";

export const Route = createFileRoute("/optimizer")({
  head: () => ({ meta: [{ title: "Prompt Optimizer — Context-Ly" }] }),
  component: Optimizer,
});

function Optimizer() {
  return (
    <AppShell title="Prompt Optimizer" subtitle="Rewrite prompts for clarity and density. Side-by-side, with token deltas."
      actions={<button className="rounded-pill bg-foreground px-4 py-2 text-[13px] font-medium text-background hover:opacity-90"><Sparkles className="inline h-3.5 w-3.5 mr-1" /> Optimize</button>}
    >
      <div className="grid gap-5 md:grid-cols-3">
        <Stat label="Token reduction" value="68%" tone="text-success" />
        <Stat label="Context improvement" value="+34%" tone="text-success" />
        <Stat label="Quality score" value="93" tone="text-foreground" />
      </div>

      <div className="mt-6 grid gap-5 lg:grid-cols-2">
        <div className="surface-card overflow-hidden">
          <div className="flex items-center justify-between border-b border-border px-5 py-3">
            <div className="text-[13px] font-medium">Original prompt</div>
            <div className="text-mono text-[12px] text-muted-foreground">1,842 tokens</div>
          </div>
          <pre className="text-mono p-5 text-[12.5px] leading-relaxed whitespace-pre-wrap text-foreground/80">{`So I have this codebase right, and it's basically a Node.js app that uses Express and there's this thing called express-session that we use for auth and the cookies and all that stuff. We've been doing it that way for a while, but now we want to move to JWTs because it's stateless and easier to scale and works better with our mobile apps and stuff. Can you help me figure out how to do this without breaking everything? Like we need to keep the old way working for a while because there are still active sessions and our customers would be really upset if they got logged out…`}</pre>
        </div>
        <div className="surface-card overflow-hidden ring-1 ring-primary/30">
          <div className="flex items-center justify-between border-b border-border px-5 py-3">
            <div className="flex items-center gap-2 text-[13px] font-medium"><Sparkles className="h-3.5 w-3.5 text-primary" /> Optimized prompt</div>
            <div className="text-mono text-[12px] text-success">589 tokens · −68%</div>
          </div>
          <pre className="text-mono p-5 text-[12.5px] leading-relaxed whitespace-pre-wrap">{`# Role
Senior backend engineer.

# Goal
Migrate Express auth from express-session to JWT with refresh tokens.

# Constraints
- Keep existing sessions working for 30 days.
- No breaking API changes.
- Stateless on the new path.

# Deliverables
- Step-by-step migration plan
- Code diffs for affected modules
- Rollback strategy`}</pre>
        </div>
      </div>

      <div className="mt-6 flex items-center justify-center gap-2 text-[13px] text-muted-foreground">
        Send optimized prompt to <span className="rounded-pill border border-border bg-surface px-3 py-1 text-foreground">GPT-4o</span>
        <ArrowRight className="h-3.5 w-3.5" /> AI Workspace
      </div>
    </AppShell>
  );
}

function Stat({ label, value, tone }: any) {
  return (
    <div className="surface-card p-6">
      <div className="text-[13px] text-muted-foreground">{label}</div>
      <div className={`text-display mt-3 text-[40px] font-semibold ${tone}`}>{value}</div>
    </div>
  );
}

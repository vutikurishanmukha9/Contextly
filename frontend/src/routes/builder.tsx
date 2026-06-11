import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/app/AppShell";
import { FileText, Target, Shield, BookOpen, Paperclip, GripVertical, Plus, Sparkles } from "lucide-react";

export const Route = createFileRoute("/builder")({
  head: () => ({ meta: [{ title: "Context Builder — Context-Ly" }] }),
  component: Builder,
});

function Builder() {
  return (
    <AppShell
      title="Context Builder"
      subtitle="Compose goals, constraints, examples and files into a living context pack."
      actions={
        <>
          <button className="rounded-pill border border-border bg-surface px-4 py-2 text-[13px] font-medium hover:bg-muted">Save draft</button>
          <button className="rounded-pill bg-foreground px-4 py-2 text-[13px] font-medium text-background hover:opacity-90">Generate prompt</button>
        </>
      }
    >
      <div className="grid gap-5 lg:grid-cols-[260px_1fr_320px]">
        <Sources />
        <Canvas />
        <Optimizer />
      </div>
    </AppShell>
  );
}

const sources = [
  { icon: Target, label: "Goal", desc: "What does success look like?" },
  { icon: BookOpen, label: "Background", desc: "What does the model need to know?" },
  { icon: Shield, label: "Constraints", desc: "Boundaries, tone, format." },
  { icon: FileText, label: "Examples", desc: "Few-shot, gold standard, anti-examples." },
  { icon: Paperclip, label: "Files", desc: "PDFs, docs, code, transcripts." },
];

function Sources() {
  return (
    <div className="surface-card p-4">
      <div className="px-1 pb-2 text-[11px] font-medium uppercase tracking-wider text-muted-foreground">Input sources</div>
      <div className="space-y-1.5">
        {sources.map((s) => {
          const Icon = s.icon;
          return (
            <button key={s.label} className="flex w-full items-start gap-3 rounded-md p-2.5 text-left hover:bg-muted">
              <span className="mt-0.5 inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-muted">
                <Icon className="h-4 w-4" />
              </span>
              <span>
                <span className="block text-[13.5px] font-medium">{s.label}</span>
                <span className="block text-[12px] text-muted-foreground">{s.desc}</span>
              </span>
            </button>
          );
        })}
      </div>
      <button className="mt-3 inline-flex w-full items-center justify-center gap-1.5 rounded-md border border-dashed border-border px-3 py-2 text-[12.5px] text-muted-foreground hover:bg-muted">
        <Plus className="h-3.5 w-3.5" /> New source
      </button>
    </div>
  );
}

const blocks = [
  { kind: "Goal", tone: "bg-lavender", title: "Help the user refactor an authentication module to use JWT refresh tokens.", meta: "120 tok" },
  { kind: "Background", tone: "bg-sky", title: "Stack: Node 20, Express, Postgres. Existing module uses session cookies via express-session.", meta: "360 tok" },
  { kind: "Constraints", tone: "bg-peach", title: "Maintain backwards compatibility for 30 days. No breaking API changes. Production-grade only.", meta: "180 tok" },
  { kind: "Examples", tone: "bg-mint", title: "Reference: prior PR #482 for token rotation. Avoid the pattern used in legacy/v1-auth.", meta: "220 tok" },
];

function Canvas() {
  return (
    <div className="surface-card p-5">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-display text-[16px] font-semibold">Live context canvas</div>
          <div className="text-[12.5px] text-muted-foreground">Drag to reorder. Click a block to edit.</div>
        </div>
        <div className="text-mono text-[12px] text-muted-foreground">880 / 8K tokens</div>
      </div>
      <div className="mt-5 space-y-3">
        {blocks.map((b) => (
          <div key={b.title} className={`group flex items-start gap-3 rounded-xl border border-border ${b.tone} p-4`}>
            <GripVertical className="mt-1 h-4 w-4 text-foreground/40" />
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <span className="rounded-pill bg-background/60 px-2 py-0.5 text-[11px] font-medium">{b.kind}</span>
                <span className="text-mono text-[11px] text-foreground/60">{b.meta}</span>
              </div>
              <p className="mt-2 text-[14px] leading-relaxed text-foreground/85">{b.title}</p>
            </div>
          </div>
        ))}
        <button className="flex w-full items-center justify-center gap-1.5 rounded-xl border border-dashed border-border py-4 text-[13px] text-muted-foreground hover:bg-muted">
          <Plus className="h-3.5 w-3.5" /> Add context block
        </button>
      </div>
    </div>
  );
}

function Optimizer() {
  return (
    <div className="space-y-5">
      <div className="surface-card p-5">
        <div className="text-[12px] font-medium uppercase tracking-wider text-muted-foreground">Context score</div>
        <div className="text-display mt-2 text-[40px] font-semibold">94</div>
        <div className="mt-2 h-1.5 overflow-hidden rounded-pill bg-muted">
          <div className="h-full score-gradient" style={{ width: "94%" }} />
        </div>
        <div className="mt-4 space-y-2">
          {[["Relevance",96],["Completeness",91],["Redundancy",88],["Clarity",97]].map(([k,v]) => (
            <div key={k as string} className="flex items-center justify-between text-[12.5px]">
              <span className="text-muted-foreground">{k}</span><span className="text-mono">{v}</span>
            </div>
          ))}
        </div>
      </div>
      <div className="surface-card p-5">
        <div className="flex items-center gap-2 text-[12px] font-medium uppercase tracking-wider text-muted-foreground">
          <Sparkles className="h-3.5 w-3.5 text-primary" /> Suggestions
        </div>
        <ul className="mt-3 space-y-3 text-[13px]">
          <li className="rounded-md bg-muted/50 p-3">Compress "Background" — 38% redundant with prior pack.</li>
          <li className="rounded-md bg-muted/50 p-3">Add an anti-example for token rotation edge cases.</li>
          <li className="rounded-md bg-muted/50 p-3">Tighten constraints to one sentence for clarity.</li>
        </ul>
      </div>
      <div className="surface-card p-5">
        <div className="text-[12px] font-medium uppercase tracking-wider text-muted-foreground">Generated prompt</div>
        <pre className="text-mono mt-3 max-h-48 overflow-auto rounded-md bg-muted/60 p-3 text-[11.5px] leading-relaxed whitespace-pre-wrap">{`# Role
Senior backend engineer.

# Task
Refactor auth to JWT w/ refresh.

# Context
- Node 20, Express, PG
- Keep session cookies live 30d
- See PR #482 for rotation`}</pre>
      </div>
    </div>
  );
}

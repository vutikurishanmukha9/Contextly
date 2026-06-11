import { createFileRoute, Link } from "@tanstack/react-router";
import { SiteHeader } from "@/components/site/SiteHeader";
import { SiteFooter } from "@/components/site/SiteFooter";
import { BrandName } from "@/components/site/Logo";
import {
  Layers3, Library, Database, Gauge, Filter, BarChart3,
  ArrowRight, Check, Play, Layers, Zap, ShieldCheck,
} from "lucide-react";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Context-Ly — Stop Wasting Tokens. Start Building Context." },
      { name: "description", content: "The context-engineering workspace for AI. Build, compress and score context that gets sharper answers with fewer tokens." },
    ],
  }),
  component: Landing,
});

function Landing() {
  return (
    <div className="min-h-screen bg-background">
      <SiteHeader />
      <Hero />
      <LogoStrip />
      <PipelineSection />
      <FeatureGrid />
      <ContextScoreSection />
      <WorkflowSection />
      <Comparison />
      <CTA />
      <SiteFooter />
    </div>
  );
}

function Hero() {
  return (
    <section className="relative overflow-hidden">
      <div className="absolute inset-0 grid-bg opacity-60 [mask-image:radial-gradient(ellipse_at_top,black,transparent_70%)]" />
      <div className="relative mx-auto max-w-7xl px-6 pt-10 pb-12 md:pt-14 md:pb-16">
        <div className="mx-auto max-w-3xl text-center">
          <div className="inline-flex items-center gap-2 rounded-pill border border-border bg-surface px-3 py-1 text-[12.5px] text-muted-foreground">
            <span className="h-1.5 w-1.5 rounded-full bg-success" />
            Context Engine v1 — now in public preview
          </div>
          <h1 className="text-display mt-6 text-[56px] font-semibold leading-[1.02] md:text-[76px]">
            Stop wasting tokens.<br />
            <span className="text-muted-foreground">Start building </span>context.
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-[17px] leading-relaxed text-muted-foreground">
            <BrandName /> transforms messy thoughts into AI-ready context that generates sharper answers with fewer tokens. The operating system for context engineering.
          </p>
          <div className="mt-9 flex flex-wrap items-center justify-center gap-3">
            <Link to="/dashboard" className="inline-flex items-center gap-2 rounded-pill bg-foreground px-5 py-3 text-[14px] font-medium text-background hover:opacity-90">
              Start building context <ArrowRight className="h-4 w-4" />
            </Link>
            <button className="inline-flex items-center gap-2 rounded-pill border border-border bg-surface px-5 py-3 text-[14px] font-medium hover:bg-muted">
              <Play className="h-3.5 w-3.5" /> Watch demo
            </button>
          </div>
          <div className="mt-5 text-[12.5px] text-muted-foreground">
            Free during preview · No credit card · Works with OpenAI, Anthropic, Mistral, Llama
          </div>
        </div>

        <div className="relative mx-auto mt-12 max-w-6xl">
          <HeroVisual />
        </div>
      </div>
    </section>
  );
}

function HeroVisual() {
  const steps = [
    { label: "Raw Information", tokens: "12,480", tone: "bg-peach" },
    { label: "Context Processing", tokens: "8,210", tone: "bg-cream" },
    { label: "Compression", tokens: "4,920", tone: "bg-sky" },
    { label: "Optimization", tokens: "2,140", tone: "bg-lavender" },
    { label: "AI Response", tokens: "1,420", tone: "bg-mint" },
  ];
  return (
    <div className="surface-panel overflow-hidden shadow-lift">
      <div className="flex items-center justify-between border-b border-border px-5 py-3">
        <div className="flex items-center gap-2">
          <span className="h-2.5 w-2.5 rounded-full bg-[#FF5F57]" />
          <span className="h-2.5 w-2.5 rounded-full bg-[#FEBC2E]" />
          <span className="h-2.5 w-2.5 rounded-full bg-[#28C840]" />
          <span className="ml-3 text-mono text-[11.5px] text-muted-foreground">context-engine · pipeline.live</span>
        </div>
        <div className="hidden items-center gap-2 text-[12px] text-muted-foreground md:flex">
          <Zap className="h-3.5 w-3.5 text-success" />
          88.6% token reduction · realtime
        </div>
      </div>
      <div className="grid gap-4 p-6 md:grid-cols-5">
        {steps.map((s, i) => (
          <div key={s.label} className="relative">
            <div className={`rounded-xl ${s.tone} p-4 ring-1 ring-border/60`}>
              <div className="text-[11px] font-medium uppercase tracking-wider text-foreground/60">Stage {i + 1}</div>
              <div className="text-display mt-3 text-[18px] font-semibold">{s.label}</div>
              <div className="text-mono mt-6 text-[13px] text-foreground/80">{s.tokens} tok</div>
              <div className="mt-3 h-1.5 w-full overflow-hidden rounded-pill bg-foreground/10">
                <div className="h-full rounded-pill bg-foreground/70" style={{ width: `${100 - i * 18}%` }} />
              </div>
            </div>
            {i < steps.length - 1 && (
              <div className="absolute right-[-14px] top-1/2 hidden -translate-y-1/2 text-muted-foreground md:block">→</div>
            )}
          </div>
        ))}
      </div>
      <div className="grid gap-px bg-border md:grid-cols-4">
        {[
          ["Context Score", "94", "/ 100"],
          ["Tokens saved", "11,060", "this session"],
          ["Compression", "88.6%", "lossless intent"],
          ["Quality lift", "+34%", "vs. raw prompt"],
        ].map(([k, v, sub]) => (
          <div key={k} className="bg-surface px-5 py-4">
            <div className="text-[12px] text-muted-foreground">{k}</div>
            <div className="text-display mt-1 text-[22px] font-semibold">{v}</div>
            <div className="text-[11.5px] text-muted-foreground">{sub}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

function LogoStrip() {
  const names = ["OPENAI", "ANTHROPIC", "MISTRAL", "COHERE", "LLAMA", "GEMINI", "GROQ"];
  return (
    <section className="border-y border-border bg-surface">
      <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-6 px-6 py-8">
        <span className="text-[12px] uppercase tracking-wider text-muted-foreground">Works with every major model</span>
        <div className="flex flex-wrap items-center gap-x-10 gap-y-3 text-[13px] font-medium tracking-[0.15em] text-foreground/60">
          {names.map((n) => <span key={n}>{n}</span>)}
        </div>
      </div>
    </section>
  );
}

function PipelineSection() {
  return (
    <section className="mx-auto max-w-7xl px-6 py-14">
      <div className="max-w-2xl">
        <div className="text-[12px] font-medium uppercase tracking-wider text-primary">The Context Engine</div>
        <h2 className="text-display mt-3 text-[42px] font-semibold leading-tight">
          A purpose-built workspace for the work that happens <em className="font-normal text-muted-foreground">before</em> the prompt.
        </h2>
        <p className="mt-5 text-[16px] leading-relaxed text-muted-foreground">
          <BrandName /> sits between your knowledge and your model. Compose context blocks, score them in realtime, and ship optimized packs that any LLM can understand instantly.
        </p>
      </div>
    </section>
  );
}

const features = [
  { icon: Layers3, title: "Context Builder", desc: "Compose goals, constraints, examples and files into a single living canvas.", tone: "bg-lavender" },
  { icon: Filter, title: "Prompt Optimizer", desc: "Rewrite prompts for clarity and density — side-by-side with token deltas.", tone: "bg-mint" },
  { icon: Database, title: "Memory Vault", desc: "Persistent project memory, personal facts, reusable snippets and templates.", tone: "bg-sky" },
  { icon: Gauge, title: "Context Scoring", desc: "Relevance, completeness, redundancy and clarity — graded in realtime.", tone: "bg-peach" },
  { icon: Library, title: "Context Library", desc: "A searchable, taggable home for every context pack your team ships.", tone: "bg-cream" },
  { icon: BarChart3, title: "Analytics", desc: "Track tokens saved, quality lift and model performance across projects.", tone: "bg-lavender" },
];

function FeatureGrid() {
  return (
    <section className="border-y border-border bg-surface">
      <div className="mx-auto max-w-7xl px-6 py-14">
        <div className="grid gap-8 md:grid-cols-3">
          {features.map((f) => {
            const Icon = f.icon;
            return (
              <div key={f.title} className="group relative overflow-hidden rounded-xl border border-border bg-background p-6 transition-all hover:shadow-soft">
                <div className={`mb-5 inline-flex h-10 w-10 items-center justify-center rounded-md ${f.tone}`}>
                  <Icon className="h-5 w-5 text-foreground/80" />
                </div>
                <div className="text-display text-[18px] font-semibold">{f.title}</div>
                <p className="mt-2 text-[14px] leading-relaxed text-muted-foreground">{f.desc}</p>
                <div className="mt-6 h-24 rounded-md border border-border bg-surface p-3">
                  <MicroViz />
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}

function MicroViz() {
  const bars = [40, 64, 28, 80, 52, 36, 70, 44, 58];
  return (
    <div className="flex h-full items-end gap-1.5">
      {bars.map((h, i) => (
        <div key={i} className="flex-1 rounded-sm bg-foreground/10" style={{ height: `${h}%` }} />
      ))}
    </div>
  );
}

function ContextScoreSection() {
  return (
    <section className="mx-auto max-w-7xl px-6 py-14">
      <div className="grid items-center gap-12 md:grid-cols-2">
        <div>
          <div className="text-[12px] font-medium uppercase tracking-wider text-primary">Context Score</div>
          <h2 className="text-display mt-3 text-[40px] font-semibold leading-tight">
            Every context pack, graded — before it touches a model.
          </h2>
          <p className="mt-5 text-[16px] leading-relaxed text-muted-foreground">
            A composite score across four dimensions tells you exactly what to fix. No more guessing why the model went off the rails.
          </p>
          <ul className="mt-6 space-y-3">
            {["Relevance — is every block earning its tokens?", "Completeness — does the model have what it needs?", "Redundancy — what can be safely removed?", "Clarity — is intent unambiguous?"].map((t) => (
              <li key={t} className="flex items-start gap-2 text-[14.5px]">
                <Check className="mt-0.5 h-4 w-4 text-success" />
                {t}
              </li>
            ))}
          </ul>
        </div>
        <div className="surface-panel p-8 shadow-soft">
          <div className="flex items-baseline justify-between">
            <div>
              <div className="text-[12px] text-muted-foreground">Overall Context Score</div>
              <div className="text-display mt-1 text-[64px] font-semibold leading-none">94</div>
            </div>
            <div className="rounded-pill bg-mint px-3 py-1 text-[12px] font-medium text-foreground/70">Excellent</div>
          </div>
          <div className="mt-6 h-2 w-full overflow-hidden rounded-pill bg-muted">
            <div className="h-full score-gradient" style={{ width: "94%" }} />
          </div>
          <div className="mt-8 grid grid-cols-2 gap-6">
            {[["Relevance", 96],["Completeness", 91],["Redundancy", 88],["Clarity", 97]].map(([k, v]) => (
              <div key={k as string}>
                <div className="flex items-baseline justify-between">
                  <span className="text-[13px] text-muted-foreground">{k}</span>
                  <span className="text-mono text-[13px]">{v}</span>
                </div>
                <div className="mt-2 h-1.5 w-full overflow-hidden rounded-pill bg-muted">
                  <div className="h-full rounded-pill bg-foreground/80" style={{ width: `${v as number}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

function WorkflowSection() {
  const steps = [
    { n: "01", title: "Capture", desc: "Pull in goals, files, constraints, examples and prior conversations." },
    { n: "02", title: "Compose", desc: "Drag context blocks into a living canvas. Reorder, group, collapse." },
    { n: "03", title: "Score", desc: "Realtime grading across four axes. Concrete suggestions to lift quality." },
    { n: "04", title: "Ship", desc: "Export an optimized pack or send straight into the AI Workspace." },
  ];
  return (
    <section className="border-y border-border bg-surface">
      <div className="mx-auto max-w-7xl px-6 py-14">
        <div className="text-display text-[40px] font-semibold leading-tight">From scattered notes to a precision context pack.</div>
        <div className="mt-12 grid gap-px overflow-hidden rounded-xl border border-border md:grid-cols-4">
          {steps.map((s) => (
            <div key={s.n} className="bg-background p-6">
              <div className="text-mono text-[12px] text-muted-foreground">{s.n}</div>
              <div className="text-display mt-3 text-[20px] font-semibold">{s.title}</div>
              <p className="mt-2 text-[14px] leading-relaxed text-muted-foreground">{s.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function Comparison() {
  const rows = [
    ["Token efficiency", "Manual trial & error", "Realtime compression & scoring"],
    ["Reusable context", "Copy/paste across chats", "Memory Vault + Library"],
    ["Quality feedback", "Re-prompt until it works", "Four-axis Context Score"],
    ["Team workflows", "Shared docs, lost prompts", "Versioned context packs"],
  ];
  return (
    <section className="mx-auto max-w-7xl px-6 py-14">
      <div className="text-display text-[40px] font-semibold leading-tight">Raw chat vs. context engineering.</div>
      <div className="mt-10 overflow-hidden rounded-xl border border-border">
        <div className="grid grid-cols-3 bg-muted px-6 py-3 text-[12px] font-medium uppercase tracking-wider text-muted-foreground">
          <div>Dimension</div><div>Vanilla chatbots</div><div className="text-foreground">With <BrandName /></div>
        </div>
        {rows.map(([a, b, c]) => (
          <div key={a} className="grid grid-cols-3 items-center border-t border-border bg-surface px-6 py-5 text-[14px]">
            <div className="font-medium">{a}</div>
            <div className="text-muted-foreground">{b}</div>
            <div className="flex items-center gap-2"><Check className="h-4 w-4 text-success" />{c}</div>
          </div>
        ))}
      </div>
    </section>
  );
}

function CTA() {
  return (
    <section className="mx-auto max-w-7xl px-6 pb-14">
      <div className="relative overflow-hidden rounded-2xl border border-border bg-foreground p-12 text-background md:p-16">
        <div className="relative max-w-2xl">
          <h2 className="text-display text-[44px] font-semibold leading-[1.05]">
            Less noise. Better context. Smarter AI.
          </h2>
          <p className="mt-4 text-[16px] leading-relaxed text-background/70">
            Join thousands of teams shipping context packs instead of throwaway prompts.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link to="/dashboard" className="inline-flex items-center gap-2 rounded-pill bg-background px-5 py-3 text-[14px] font-medium text-foreground hover:opacity-90">
              Start free <ArrowRight className="h-4 w-4" />
            </Link>
            <Link to="/pricing" className="inline-flex items-center gap-2 rounded-pill border border-background/20 px-5 py-3 text-[14px] font-medium text-background hover:bg-background/10">
              See pricing
            </Link>
          </div>
          <div className="mt-8 flex flex-wrap items-center gap-6 text-[12.5px] text-background/60">
            <span className="inline-flex items-center gap-1.5"><ShieldCheck className="h-3.5 w-3.5" /> SOC2-ready</span>
            <span className="inline-flex items-center gap-1.5"><Layers className="h-3.5 w-3.5" /> Bring your own keys</span>
            <span className="inline-flex items-center gap-1.5"><Zap className="h-3.5 w-3.5" /> 88% avg token savings</span>
          </div>
        </div>
      </div>
    </section>
  );
}

import { createFileRoute, Link } from "@tanstack/react-router";
import { SiteHeader } from "@/components/site/SiteHeader";
import { SiteFooter } from "@/components/site/SiteFooter";
import { Check } from "lucide-react";

export const Route = createFileRoute("/pricing")({
  head: () => ({ meta: [{ title: "Pricing — Context-Ly" }, { name: "description", content: "Simple, usage-friendly pricing for context engineering." }] }),
  component: Pricing,
});

const tiers = [
  { name: "Starter", price: "$0", sub: "For individuals exploring context engineering.",
    features: ["3 context packs","Memory Vault (50 entries)","Context Score Analyzer","Single workspace","Community support"], cta: "Start free", tone: "" },
  { name: "Pro", price: "$24", sub: "For builders shipping AI features every week.",
    features: ["Unlimited context packs","Memory Vault (unlimited)","Prompt Optimizer","Analytics dashboard","BYOK · OpenAI / Anthropic / Mistral","Email support"], cta: "Start Pro", tone: "ring-2 ring-foreground" },
  { name: "Team", price: "$59", sub: "For teams standardising on context as infrastructure.",
    features: ["Everything in Pro","Shared library & memory","Roles & permissions","Versioned context packs","SSO + SOC2","Priority support"], cta: "Start Team", tone: "" },
];

function Pricing() {
  return (
    <div className="min-h-screen bg-background">
      <SiteHeader />
      <section className="mx-auto max-w-7xl px-6 py-20">
        <div className="mx-auto max-w-2xl text-center">
          <div className="text-[12px] font-medium uppercase tracking-wider text-primary">Pricing</div>
          <h1 className="text-display mt-3 text-[52px] font-semibold leading-tight">Pay for context, not chat tokens.</h1>
          <p className="mt-4 text-[16px] text-muted-foreground">Simple plans. No per-seat surprises. Cancel any time.</p>
        </div>
        <div className="mt-14 grid gap-5 md:grid-cols-3">
          {tiers.map((t) => (
            <div key={t.name} className={`surface-panel p-8 ${t.tone}`}>
              <div className="text-display text-[18px] font-semibold">{t.name}</div>
              <div className="text-[13px] text-muted-foreground">{t.sub}</div>
              <div className="mt-6 flex items-baseline gap-1">
                <span className="text-display text-[44px] font-semibold">{t.price}</span>
                <span className="text-[13px] text-muted-foreground">/ month</span>
              </div>
              <Link to="/dashboard" className={`mt-6 inline-flex w-full items-center justify-center rounded-pill px-4 py-2.5 text-[13.5px] font-medium ${t.tone ? "bg-foreground text-background" : "border border-border bg-surface hover:bg-muted"}`}>{t.cta}</Link>
              <ul className="mt-7 space-y-2.5 text-[13.5px]">
                {t.features.map((f) => (
                  <li key={f} className="flex items-start gap-2"><Check className="mt-0.5 h-4 w-4 text-success" />{f}</li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="mt-14 surface-panel p-8 md:p-12">
          <div className="grid items-center gap-6 md:grid-cols-3">
            <div className="md:col-span-2">
              <div className="text-display text-[26px] font-semibold leading-snug">Enterprise — context as infrastructure for your AI org.</div>
              <p className="mt-2 text-[14px] text-muted-foreground">Private deployment, custom retention, audit trails, dedicated success.</p>
            </div>
            <div className="md:text-right">
              <button className="rounded-pill border border-border bg-surface px-5 py-3 text-[14px] font-medium hover:bg-muted">Talk to sales</button>
            </div>
          </div>
        </div>
      </section>
      <SiteFooter />
    </div>
  );
}

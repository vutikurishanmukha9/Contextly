import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/app/AppShell";
import { CheckCircle2, AlertCircle } from "lucide-react";

export const Route = createFileRoute("/analyzer")({
  head: () => ({ meta: [{ title: "Context Score Analyzer — Context-Ly" }] }),
  component: Analyzer,
});

function Analyzer() {
  return (
    <AppShell title="Context Score Analyzer" subtitle="Realtime grading across relevance, completeness, redundancy and clarity.">
      <div className="grid gap-5 lg:grid-cols-3">
        <div className="surface-panel p-8 lg:col-span-1">
          <div className="text-[12px] text-muted-foreground">Overall score</div>
          <div className="text-display mt-2 text-[80px] font-semibold leading-none">87</div>
          <div className="mt-3 inline-flex rounded-pill bg-mint px-2.5 py-0.5 text-[12px] font-medium">Good</div>
          <div className="mt-6 h-2 overflow-hidden rounded-pill bg-muted">
            <div className="h-full score-gradient" style={{ width: "87%" }} />
          </div>
          <div className="mt-8 space-y-4">
            {[["Relevance",92,"Strong signal-to-noise ratio."],["Completeness",84,"Missing one edge-case example."],["Redundancy",78,"Two blocks overlap by ~30%."],["Clarity",94,"Intent is unambiguous."]].map(([k,v,n]) => (
              <div key={k as string}>
                <div className="flex items-baseline justify-between">
                  <span className="text-[13px] font-medium">{k}</span>
                  <span className="text-mono text-[13px]">{v}</span>
                </div>
                <div className="mt-1.5 h-1.5 overflow-hidden rounded-pill bg-muted">
                  <div className="h-full rounded-pill bg-foreground/80" style={{ width: `${v as number}%` }} />
                </div>
                <div className="mt-1 text-[12px] text-muted-foreground">{n}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="surface-card p-6 lg:col-span-2">
          <div className="text-display text-[16px] font-semibold">Recommendations</div>
          <div className="mt-4 space-y-3">
            {[
              ["warn", "Redundancy detected", "Block #3 (Background) and Block #6 (Project facts) overlap. Merge or compress."],
              ["good", "Strong constraints", "Constraints are scoped and testable. Keep them."],
              ["warn", "Add anti-example", "Models drift on edge-cases. One anti-example would lift completeness by ~6 pts."],
              ["good", "Token budget healthy", "You're using 28% of the model's effective context window."],
              ["warn", "Clarify pronouns", "Block #4 uses 'it' ambiguously. Replace with explicit nouns."],
            ].map(([k, t, d], i) => (
              <div key={i} className="flex items-start gap-3 rounded-lg border border-border bg-background p-4">
                {k === "good" ? <CheckCircle2 className="mt-0.5 h-4 w-4 text-success" /> : <AlertCircle className="mt-0.5 h-4 w-4 text-warning" />}
                <div className="min-w-0">
                  <div className="text-[14px] font-medium">{t}</div>
                  <div className="mt-0.5 text-[13px] text-muted-foreground">{d}</div>
                </div>
                <button className="ml-auto rounded-pill border border-border px-3 py-1 text-[12px] hover:bg-muted">Apply</button>
              </div>
            ))}
          </div>
        </div>
      </div>
    </AppShell>
  );
}

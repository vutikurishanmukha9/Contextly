import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/app/AppShell";

export const Route = createFileRoute("/analytics")({
  head: () => ({ meta: [{ title: "Analytics — Context-Ly" }] }),
  component: Analytics,
});

function Analytics() {
  return (
    <AppShell title="Analytics" subtitle="Token savings, context effectiveness and model performance across projects.">
      <div className="grid gap-5 md:grid-cols-4">
        {[
          ["Tokens saved", "1.24M", "+22% MoM"],
          ["Avg context score", "91", "+4 pts"],
          ["Prompts shipped", "8,420", "+612 this week"],
          ["Quality lift", "+34%", "vs. raw prompts"],
        ].map(([k,v,s]) => (
          <div key={k} className="surface-card p-6">
            <div className="text-[13px] text-muted-foreground">{k}</div>
            <div className="text-display mt-3 text-[34px] font-semibold">{v}</div>
            <div className="mt-1 text-[12.5px] text-success">{s}</div>
          </div>
        ))}
      </div>

      <div className="mt-5 grid gap-5 lg:grid-cols-3">
        <div className="surface-card p-6 lg:col-span-2">
          <div className="text-display text-[16px] font-semibold">Tokens processed vs. sent to model</div>
          <Chart />
        </div>
        <div className="surface-card p-6">
          <div className="text-display text-[16px] font-semibold">Score distribution</div>
          <div className="mt-6 space-y-3">
            {[["A · 90–100", 58],["B · 80–89", 28],["C · 70–79", 10],["D · <70", 4]].map(([k,v]) => (
              <div key={k as string}>
                <div className="flex items-baseline justify-between text-[13px]"><span>{k}</span><span className="text-mono">{v}%</span></div>
                <div className="mt-1.5 h-1.5 overflow-hidden rounded-pill bg-muted">
                  <div className="h-full rounded-pill bg-foreground/80" style={{ width: `${v as number}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="mt-5 surface-card p-6">
        <div className="text-display text-[16px] font-semibold">Model performance</div>
        <div className="mt-5 overflow-hidden rounded-lg border border-border">
          <div className="grid grid-cols-5 bg-muted px-4 py-2.5 text-[12px] font-medium uppercase tracking-wider text-muted-foreground">
            <div className="col-span-2">Model</div><div>Avg score</div><div>Avg tokens</div><div>Cost / prompt</div>
          </div>
          {[
            ["GPT-4o", 94, "1,420", "$0.018"],
            ["Claude Sonnet", 91, "1,640", "$0.014"],
            ["Mistral Large", 88, "1,820", "$0.009"],
            ["Llama 3.1 70B", 84, "2,120", "$0.004"],
          ].map((r) => (
            <div key={r[0] as string} className="grid grid-cols-5 items-center border-t border-border bg-surface px-4 py-3 text-[13.5px]">
              <div className="col-span-2 font-medium">{r[0]}</div>
              <div className="text-mono">{r[1]}</div>
              <div className="text-mono">{r[2]}</div>
              <div className="text-mono">{r[3]}</div>
            </div>
          ))}
        </div>
      </div>
    </AppShell>
  );
}

function Chart() {
  const a = [40,52,48,68,60,82,76,90,84,98,92,110];
  const b = [10,14,12,20,16,26,22,30,24,32,28,36];
  const max = 120, w = 100, h = 60;
  const pts = (arr: number[]) => arr.map((v,i)=>`${(i*w)/(arr.length-1)},${h-(v/max)*h}`).join(" ");
  const area = (arr: number[]) => `0,${h} ${pts(arr)} ${w},${h}`;
  return (
    <svg viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none" className="mt-6 h-56 w-full">
      <polygon fill="rgba(94,106,210,0.08)" points={area(a)} />
      <polyline fill="none" stroke="rgba(17,17,17,0.25)" strokeWidth="0.6" points={pts(a)} />
      <polyline fill="none" stroke="var(--primary)" strokeWidth="1.2" points={pts(b)} />
    </svg>
  );
}

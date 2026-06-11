import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/app/AppShell";
import { Search, Filter, Tag } from "lucide-react";

export const Route = createFileRoute("/library")({
  head: () => ({ meta: [{ title: "Context Library — Context-Ly" }] }),
  component: LibraryPage,
});

const packs = [
  { title: "Customer support onboarding", tag: "Support", tone: "bg-mint", tokens: "2,140", score: 94 },
  { title: "Q4 launch — marketing brief", tag: "Marketing", tone: "bg-peach", tokens: "3,820", score: 88 },
  { title: "Auth refactor playbook", tag: "Engineering", tone: "bg-sky", tokens: "1,420", score: 96 },
  { title: "Enterprise demo script", tag: "Sales", tone: "bg-lavender", tokens: "2,640", score: 82 },
  { title: "Investor update — Q3", tag: "Finance", tone: "bg-cream", tokens: "1,820", score: 90 },
  { title: "Brand voice — long form", tag: "Brand", tone: "bg-mint", tokens: "1,210", score: 92 },
  { title: "Bug triage assistant", tag: "Engineering", tone: "bg-sky", tokens: "980", score: 87 },
  { title: "Recruiting outreach", tag: "People", tone: "bg-peach", tokens: "1,640", score: 84 },
  { title: "RFP response template", tag: "Sales", tone: "bg-lavender", tokens: "2,920", score: 89 },
];

function LibraryPage() {
  return (
    <AppShell title="Context Library" subtitle="Every pack your team has ever shipped — searchable, taggable, versioned."
      actions={<button className="rounded-pill bg-foreground px-4 py-2 text-[13px] font-medium text-background hover:opacity-90">New pack</button>}
    >
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex w-full max-w-md items-center gap-2 rounded-md border border-border bg-surface px-3 py-2">
          <Search className="h-3.5 w-3.5 text-muted-foreground" />
          <input className="flex-1 bg-transparent text-[13px] outline-none placeholder:text-muted-foreground" placeholder="Search packs, tags, content…" />
        </div>
        <button className="inline-flex items-center gap-1.5 rounded-md border border-border bg-surface px-3 py-2 text-[13px]"><Filter className="h-3.5 w-3.5" /> Filter</button>
        <div className="flex flex-wrap gap-1.5">
          {["All","Engineering","Marketing","Sales","Support","Brand"].map((t,i) => (
            <button key={t} className={`rounded-pill border px-3 py-1 text-[12px] ${i===0 ? "border-foreground bg-foreground text-background" : "border-border bg-surface hover:bg-muted"}`}>{t}</button>
          ))}
        </div>
      </div>

      <div className="mt-6 grid gap-5 md:grid-cols-2 lg:grid-cols-3">
        {packs.map((p) => (
          <div key={p.title} className="surface-card overflow-hidden transition-all hover:shadow-soft">
            <div className={`h-24 ${p.tone}`} />
            <div className="p-5">
              <div className="flex items-center gap-2 text-[11.5px] text-muted-foreground">
                <Tag className="h-3 w-3" /> {p.tag}
                <span className="ml-auto text-mono">{p.tokens} tok</span>
              </div>
              <div className="text-display mt-2 text-[16px] font-semibold leading-snug">{p.title}</div>
              <div className="mt-4 flex items-center gap-2">
                <div className="h-1.5 flex-1 overflow-hidden rounded-pill bg-muted">
                  <div className="h-full score-gradient" style={{ width: `${p.score}%` }} />
                </div>
                <span className="text-mono text-[12px] w-7 text-right">{p.score}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </AppShell>
  );
}

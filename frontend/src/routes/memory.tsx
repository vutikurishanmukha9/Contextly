import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/app/AppShell";
import { Folder, User, Layers, FileText, Search, Plus } from "lucide-react";

export const Route = createFileRoute("/memory")({
  head: () => ({ meta: [{ title: "Memory Vault — Context-Ly" }] }),
  component: MemoryPage,
});

const groups = [
  { icon: User, title: "Personal memory", count: 24, tone: "bg-lavender" },
  { icon: Folder, title: "Project memory", count: 58, tone: "bg-sky" },
  { icon: Layers, title: "Reusable context", count: 142, tone: "bg-mint" },
  { icon: FileText, title: "Custom templates", count: 31, tone: "bg-peach" },
];

const items = [
  ["Tone of voice", "Writes in concise, declarative sentences. Avoids jargon.", ["voice","brand"]],
  ["Codebase facts", "Monorepo via Turborepo. Bun. Drizzle on Postgres.", ["engineering","stack"]],
  ["Customer profile", "Mid-market SaaS, technical buyers, 50–500 employees.", ["sales","persona"]],
  ["Compliance posture", "SOC2 Type II. Data residency: US + EU.", ["security","ops"]],
  ["Pricing model", "Usage-based with monthly minimums.", ["billing"]],
  ["Brand colors", "Warm neutrals + accent #5E6AD2.", ["brand","design"]],
];

function MemoryPage() {
  return (
    <AppShell title="Memory Vault" subtitle="Persistent facts, snippets and templates your context packs can reference."
      actions={<button className="rounded-pill bg-foreground px-4 py-2 text-[13px] font-medium text-background hover:opacity-90">New memory</button>}
    >
      <div className="grid gap-5 md:grid-cols-4">
        {groups.map((g) => {
          const Icon = g.icon;
          return (
            <div key={g.title} className="surface-card p-5">
              <span className={`inline-flex h-9 w-9 items-center justify-center rounded-md ${g.tone}`}><Icon className="h-4 w-4" /></span>
              <div className="text-display mt-4 text-[15px] font-semibold">{g.title}</div>
              <div className="mt-1 text-[12.5px] text-muted-foreground">{g.count} entries</div>
            </div>
          );
        })}
      </div>

      <div className="mt-6 surface-card">
        <div className="flex items-center gap-3 border-b border-border p-4">
          <Search className="h-3.5 w-3.5 text-muted-foreground" />
          <input className="flex-1 bg-transparent text-[13.5px] outline-none placeholder:text-muted-foreground" placeholder="Search memory…" />
          <button className="inline-flex items-center gap-1.5 rounded-md border border-border px-3 py-1.5 text-[12.5px] hover:bg-muted"><Plus className="h-3.5 w-3.5" /> Add</button>
        </div>
        <div className="divide-y divide-border">
          {items.map(([t, d, tags]) => (
            <div key={t as string} className="grid grid-cols-12 gap-4 p-4">
              <div className="col-span-3 text-[14px] font-medium">{t}</div>
              <div className="col-span-6 text-[13.5px] text-muted-foreground">{d}</div>
              <div className="col-span-3 flex flex-wrap items-start justify-end gap-1.5">
                {(tags as string[]).map((tag) => (
                  <span key={tag} className="rounded-pill bg-muted px-2 py-0.5 text-[11px] text-muted-foreground">{tag}</span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </AppShell>
  );
}

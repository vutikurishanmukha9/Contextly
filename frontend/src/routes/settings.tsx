import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/app/AppShell";

export const Route = createFileRoute("/settings")({
  head: () => ({ meta: [{ title: "Settings — Context-Ly" }] }),
  component: Settings,
});

const tabs = ["Profile", "Workspace", "Models", "API keys", "Billing", "Members"];

function Settings() {
  return (
    <AppShell title="Settings" subtitle="Manage your workspace, models and billing.">
      <div className="grid gap-6 lg:grid-cols-[200px_1fr]">
        <nav className="space-y-0.5">
          {tabs.map((t, i) => (
            <button key={t} className={`block w-full rounded-md px-3 py-2 text-left text-[13.5px] ${i===0 ? "bg-muted text-foreground" : "text-muted-foreground hover:bg-muted/60 hover:text-foreground"}`}>{t}</button>
          ))}
        </nav>
        <div className="space-y-5">
          <Section title="Profile" desc="How you appear across the workspace.">
            <div className="flex items-center gap-4">
              <div className="h-14 w-14 rounded-full bg-gradient-to-br from-primary to-[#8B95E5]" />
              <button className="rounded-pill border border-border bg-surface px-3 py-1.5 text-[12.5px] hover:bg-muted">Upload</button>
            </div>
            <Field label="Display name" value="Ada Lovelace" />
            <Field label="Work email" value="ada@northwind.com" />
          </Section>

          <Section title="Default model" desc="Used when a context pack doesn't specify one.">
            <div className="grid gap-3 md:grid-cols-2">
              {["GPT-4o","Claude Sonnet","Mistral Large","Llama 3.1 70B"].map((m,i) => (
                <label key={m} className={`flex items-center gap-3 rounded-lg border p-3 ${i===0 ? "border-foreground bg-muted/40" : "border-border bg-surface"}`}>
                  <span className={`h-4 w-4 rounded-full border ${i===0 ? "border-foreground bg-foreground" : "border-border"}`} />
                  <span className="text-[13.5px] font-medium">{m}</span>
                </label>
              ))}
            </div>
          </Section>

          <Section title="API keys" desc="Bring your own — keys never leave your workspace.">
            <Field label="OpenAI" value="sk-•••• •••• •••• 4f29" />
            <Field label="Anthropic" value="anthrop-•••• •••• 7c12" />
          </Section>
        </div>
      </div>
    </AppShell>
  );
}

function Section({ title, desc, children }: any) {
  return (
    <div className="surface-card p-6">
      <div className="text-display text-[16px] font-semibold">{title}</div>
      <div className="text-[12.5px] text-muted-foreground">{desc}</div>
      <div className="mt-5 space-y-4">{children}</div>
    </div>
  );
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <label className="text-[12.5px] font-medium">{label}</label>
      <input defaultValue={value} className="mt-1.5 w-full rounded-md border border-input bg-surface px-3 py-2.5 text-[13.5px] outline-none focus:ring-2 focus:ring-ring/30" />
    </div>
  );
}

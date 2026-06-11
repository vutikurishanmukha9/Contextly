import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/app/AppShell";
import { Send, Paperclip, Sparkles } from "lucide-react";

export const Route = createFileRoute("/workspace")({
  head: () => ({ meta: [{ title: "AI Workspace — Context-Ly" }] }),
  component: Workspace,
});

function Workspace() {
  return (
    <AppShell title="AI Workspace" subtitle="Chat backed by your optimized context pack.">
      <div className="grid gap-5 lg:grid-cols-[1fr_300px]">
        <div className="surface-card flex flex-col" style={{ minHeight: "60vh" }}>
          <div className="flex items-center justify-between border-b border-border px-5 py-3 text-[12.5px]">
            <div className="flex items-center gap-2">
              <span className="rounded-pill bg-primary-soft px-2 py-0.5 font-medium text-accent-foreground">Pack: Auth refactor playbook</span>
              <span className="text-muted-foreground">·</span>
              <span className="text-mono text-muted-foreground">1,420 tokens attached</span>
            </div>
            <span className="rounded-pill border border-border bg-surface px-2 py-0.5">GPT-4o</span>
          </div>
          <div className="flex-1 space-y-5 overflow-y-auto p-6">
            <Msg who="you">Plan the migration in 5 steps, no code yet.</Msg>
            <Msg who="ai">
              <ol className="ml-4 list-decimal space-y-1.5">
                <li>Introduce JWT middleware behind a feature flag.</li>
                <li>Dual-issue session + JWT for 30 days.</li>
                <li>Add refresh-token rotation with revocation list.</li>
                <li>Migrate clients to JWT (mobile first, web second).</li>
                <li>Deprecate express-session; archive the module.</li>
              </ol>
              <div className="mt-3 text-[12px] text-muted-foreground">Used: Goal · Constraints · PR #482</div>
            </Msg>
            <Msg who="you">Now show the rollback strategy.</Msg>
          </div>
          <div className="border-t border-border p-3">
            <div className="flex items-end gap-2 rounded-xl border border-input bg-surface p-2">
              <button className="rounded-md p-2 text-muted-foreground hover:bg-muted"><Paperclip className="h-4 w-4" /></button>
              <textarea rows={1} placeholder="Ask anything — context pack is attached…" className="min-h-9 flex-1 resize-none bg-transparent px-1 py-1.5 text-[14px] outline-none placeholder:text-muted-foreground" />
              <button className="inline-flex items-center gap-1.5 rounded-pill bg-foreground px-3 py-2 text-[13px] font-medium text-background"><Send className="h-3.5 w-3.5" /> Send</button>
            </div>
          </div>
        </div>
        <aside className="space-y-5">
          <div className="surface-card p-5">
            <div className="text-[12px] font-medium uppercase tracking-wider text-muted-foreground">Context attached</div>
            <ul className="mt-3 space-y-2 text-[13px]">
              {["Goal · refactor auth","Constraints · 30d compat","Examples · PR #482","Memory · stack facts"].map((x) => (
                <li key={x} className="flex items-center justify-between"><span>{x}</span><span className="text-mono text-[11.5px] text-muted-foreground">~</span></li>
              ))}
            </ul>
          </div>
          <div className="surface-card p-5">
            <div className="text-[12px] font-medium uppercase tracking-wider text-muted-foreground">Response quality</div>
            <div className="text-display mt-2 text-[28px] font-semibold">A+</div>
            <div className="text-[12.5px] text-muted-foreground">Grounded · concise · within constraints</div>
          </div>
          <div className="surface-card p-5">
            <div className="flex items-center gap-2 text-[12px] font-medium uppercase tracking-wider text-muted-foreground"><Sparkles className="h-3.5 w-3.5 text-primary" /> Suggestion</div>
            <p className="mt-2 text-[13px]">Attach the "Compliance posture" memory to harden the rollback plan.</p>
          </div>
        </aside>
      </div>
    </AppShell>
  );
}

function Msg({ who, children }: { who: "you" | "ai"; children: any }) {
  if (who === "you") {
    return (
      <div className="flex justify-end">
        <div className="max-w-[75%] rounded-2xl rounded-tr-md bg-foreground px-4 py-2.5 text-[14px] text-background">{children}</div>
      </div>
    );
  }
  return (
    <div className="flex gap-3">
      <div className="h-8 w-8 shrink-0 rounded-full bg-gradient-to-br from-primary to-[#8B95E5]" />
      <div className="max-w-[75%] rounded-2xl rounded-tl-md border border-border bg-surface px-4 py-3 text-[14px]">{children}</div>
    </div>
  );
}

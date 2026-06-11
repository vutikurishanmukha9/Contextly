import { createFileRoute, Link } from "@tanstack/react-router";
import { Logo, BrandName } from "@/components/site/Logo";
import { ArrowRight } from "lucide-react";

export const Route = createFileRoute("/auth")({
  head: () => ({ meta: [{ title: "Sign in — Context-Ly" }] }),
  component: AuthPage,
});

function AuthPage() {
  return (
    <div className="grid min-h-screen md:grid-cols-2">
      <div className="flex flex-col justify-between p-10">
        <Logo />
        <div className="mx-auto w-full max-w-sm">
          <h1 className="text-display text-[34px] font-semibold leading-tight">Welcome back.</h1>
          <p className="mt-2 text-[14px] text-muted-foreground">Sign in to your context workspace.</p>
          <div className="mt-8 space-y-3">
            <button className="w-full rounded-md border border-border bg-surface px-4 py-2.5 text-[13.5px] font-medium hover:bg-muted">Continue with Google</button>
            <button className="w-full rounded-md border border-border bg-surface px-4 py-2.5 text-[13.5px] font-medium hover:bg-muted">Continue with GitHub</button>
          </div>
          <div className="my-6 flex items-center gap-3 text-[12px] text-muted-foreground">
            <div className="h-px flex-1 bg-border" /> or <div className="h-px flex-1 bg-border" />
          </div>
          <form className="space-y-3">
            <div>
              <label className="text-[12.5px] font-medium">Work email</label>
              <input className="mt-1.5 w-full rounded-md border border-input bg-surface px-3 py-2.5 text-[14px] outline-none focus:ring-2 focus:ring-ring/30" placeholder="ada@company.com" />
            </div>
            <div>
              <label className="text-[12.5px] font-medium">Password</label>
              <input type="password" className="mt-1.5 w-full rounded-md border border-input bg-surface px-3 py-2.5 text-[14px] outline-none focus:ring-2 focus:ring-ring/30" placeholder="••••••••" />
            </div>
            <Link to="/dashboard" className="mt-2 inline-flex w-full items-center justify-center gap-2 rounded-pill bg-foreground px-4 py-2.5 text-[14px] font-medium text-background hover:opacity-90">
              Sign in <ArrowRight className="h-4 w-4" />
            </Link>
          </form>
          <p className="mt-6 text-[12.5px] text-muted-foreground">New here? <Link to="/dashboard" className="text-foreground underline-offset-4 hover:underline">Create an account</Link></p>
        </div>
        <div className="text-[12px] text-muted-foreground">© <BrandName /></div>
      </div>
      <div className="hidden border-l border-border bg-surface p-10 md:flex md:flex-col md:justify-between">
        <div />
        <div className="mx-auto max-w-md">
          <div className="text-display text-[28px] font-semibold leading-snug">
            "We went from 8K-token prompts to 1.2K. Quality went up, not down."
          </div>
          <div className="mt-5 flex items-center gap-3">
            <div className="h-9 w-9 rounded-full bg-gradient-to-br from-primary to-[#8B95E5]" />
            <div>
              <div className="text-[13.5px] font-medium">Maya Chen</div>
              <div className="text-[12px] text-muted-foreground">Head of AI, Northwind</div>
            </div>
          </div>
        </div>
        <div className="grid grid-cols-3 gap-3">
          {[["88%","tokens saved"],["+34%","quality lift"],["12K+","context packs"]].map(([v,l]) => (
            <div key={l} className="rounded-lg border border-border bg-background p-4">
              <div className="text-display text-[20px] font-semibold">{v}</div>
              <div className="text-[11.5px] text-muted-foreground">{l}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

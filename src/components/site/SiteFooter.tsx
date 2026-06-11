import { Logo, BrandName } from "./Logo";
import { Link } from "@tanstack/react-router";

export function SiteFooter() {
  return (
    <footer className="border-t border-border bg-background">
      <div className="mx-auto grid max-w-7xl grid-cols-2 gap-10 px-6 py-16 md:grid-cols-5">
        <div className="col-span-2 max-w-sm">
          <Logo />
          <p className="mt-4 text-[14px] leading-relaxed text-muted-foreground">
            The operating system for AI context engineering. Less noise. Better context. Smarter AI.
          </p>
        </div>
        {[
          { title: "Product", items: [["Builder","/builder"],["Library","/library"],["Memory","/memory"],["Optimizer","/optimizer"]] },
          { title: "Workspace", items: [["Dashboard","/dashboard"],["Analyzer","/analyzer"],["Workspace","/workspace"],["Analytics","/analytics"]] },
          { title: "Company", items: [["Pricing","/pricing"],["Settings","/settings"],["Sign in","/auth"]] },
        ].map((g) => (
          <div key={g.title}>
            <div className="text-[12px] font-medium uppercase tracking-wider text-muted-foreground">{g.title}</div>
            <ul className="mt-4 space-y-2.5">
              {g.items.map(([label, to]) => (
                <li key={to}>
                  <Link to={to} className="text-[14px] text-foreground/80 hover:text-foreground">{label}</Link>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
      <div className="border-t border-border">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-5 text-[12.5px] text-muted-foreground">
          <span>© {new Date().getFullYear()} <BrandName /> Labs, Inc.</span>
          <span className="text-mono">v1.0 · context-engine</span>
        </div>
      </div>
    </footer>
  );
}

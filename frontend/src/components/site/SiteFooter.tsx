import { Logo, BrandName } from "./Logo";

export function SiteFooter() {
  return (
    <footer className="border-t border-border bg-background">
      <div className="mx-auto grid max-w-7xl grid-cols-2 gap-10 px-6 py-16 md:grid-cols-5">
        <div className="col-span-2 md:col-span-5 max-w-sm">
          <Logo />
          <p className="mt-4 text-[14px] leading-relaxed text-muted-foreground">
            The operating system for AI context engineering. Less noise. Better context. Smarter AI.
          </p>
        </div>
      </div>
      <div className="border-t border-border">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-5 text-[12.5px] text-muted-foreground">
          <span>
            © {new Date().getFullYear()} <BrandName /> Labs, Inc.
          </span>
          <span className="text-mono">v1.0 · context-engine</span>
        </div>
      </div>
    </footer>
  );
}

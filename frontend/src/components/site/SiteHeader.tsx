import { Link } from "@tanstack/react-router";
import { Logo } from "./Logo";

const links = [
  { to: "/", label: "Product" },
  { to: "/pricing", label: "Pricing" },
  { to: "/dashboard", label: "Dashboard" },
  { to: "/analyzer", label: "Analyzer" },
];

export function SiteHeader() {
  return (
    <header className="sticky top-0 z-40 border-b border-border/70 bg-background/80 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
        <div className="flex items-center gap-10">
          <Logo />
          <nav className="hidden items-center gap-7 md:flex">
            {links.map((l) => (
              <Link
                key={l.to}
                to={l.to}
                className="text-[14px] text-muted-foreground transition-colors hover:text-foreground"
                activeProps={{ className: "text-foreground" }}
              >
                {l.label}
              </Link>
            ))}
          </nav>
        </div>
        <div className="flex items-center gap-2">
          <Link to="/auth" className="hidden text-[14px] text-muted-foreground hover:text-foreground sm:inline-block px-3 py-2">
            Sign in
          </Link>
          <Link
            to="/dashboard"
            className="inline-flex items-center gap-1.5 rounded-pill bg-foreground px-4 py-2 text-[13.5px] font-medium text-background transition-opacity hover:opacity-90"
          >
            Start building
            <span aria-hidden>→</span>
          </Link>
        </div>
      </div>
    </header>
  );
}

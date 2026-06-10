import { Link } from "@tanstack/react-router";

export function Logo({ className = "" }: { className?: string }) {
  return (
    <Link to="/" className={`inline-flex items-center gap-2 ${className}`}>
      <span className="relative inline-flex h-7 w-7 items-center justify-center rounded-[8px] bg-foreground text-background">
        <span className="text-mono text-[12px] font-semibold">{"{}"}</span>
      </span>
      <span className="text-display text-[18px] font-semibold tracking-tight">
        Context<span className="text-primary">·</span>ly
      </span>
    </Link>
  );
}

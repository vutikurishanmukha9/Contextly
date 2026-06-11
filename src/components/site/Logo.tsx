import { Link } from "@tanstack/react-router";

export function Logo({ className = "" }: { className?: string }) {
  return (
    <Link to="/" className={`inline-flex items-baseline ${className}`}>
      <span
        className="text-display text-[24px] font-extrabold tracking-[-0.04em] text-foreground"
        style={{ fontWeight: 900 }}
      >
        Context
      </span>
      <span
        className="ml-[2px] text-[20px] font-medium italic text-primary"
        style={{ fontFamily: '"Playfair Display", "Times New Roman", Georgia, serif' }}
      >
        ly
      </span>
    </Link>
  );
}

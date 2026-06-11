import { Link } from "@tanstack/react-router";

type Props = {
  className?: string;
  /** Render as plain inline span (no link, inherits size) */
  inline?: boolean;
  /** Tailwind size class for the "Context" word when used as logo */
  size?: string;
};

export function BrandName({ inline = false, className = "" }: { inline?: boolean; className?: string }) {
  return (
    <span className={`whitespace-nowrap ${className}`}>
      <span
        className="font-extrabold tracking-[-0.04em] text-foreground"
        style={{ fontWeight: 900 }}
      >
        Context
      </span>
      <span
        className="italic text-primary"
        style={{
          fontFamily: '"Playfair Display", "Times New Roman", Georgia, serif',
          fontSize: "0.9em",
          marginLeft: "1px",
        }}
      >
        ly
      </span>
    </span>
  );
}

export function Logo({ className = "", size = "text-[24px]" }: Props) {
  return (
    <Link to="/" className={`inline-flex items-baseline ${className}`}>
      <span
        className={`text-display ${size} font-extrabold tracking-[-0.04em] text-foreground`}
        style={{ fontWeight: 900 }}
      >
        Context
      </span>
      <span
        className="ml-[2px] text-[0.84em] font-medium italic text-primary"
        style={{ fontFamily: '"Playfair Display", "Times New Roman", Georgia, serif' }}
      >
        ly
      </span>
    </Link>
  );
}

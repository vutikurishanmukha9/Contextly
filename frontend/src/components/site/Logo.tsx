import { Link } from "@tanstack/react-router";

type Props = {
  className?: string;
  /** Render as plain inline span (no link, inherits size) */
  inline?: boolean;
  /** Tailwind size class for the "Context" word when used as logo */
  size?: string;
};

export function BrandName({
  inline = false,
  className = "",
  size = "",
  innerClassName = "",
}: {
  inline?: boolean;
  className?: string;
  size?: string;
  innerClassName?: string;
}) {
  return (
    <span
      className={`whitespace-nowrap inline-flex items-baseline ${size} ${className} ${innerClassName}`}
    >
      <span
        className="font-extrabold tracking-[-0.04em] text-foreground"
        style={{ fontWeight: 900 }}
      >
        Context
      </span>
      <span
        className="italic text-primary ml-[2px] font-medium"
        style={{
          fontFamily: '"Playfair Display", "Times New Roman", Georgia, serif',
          fontSize: "0.84em",
        }}
      >
        ly
      </span>
    </span>
  );
}

export function Logo({ className = "", size = "text-[24px]" }: Props) {
  return (
    <Link to="/" className={className}>
      <BrandName size={size} innerClassName="text-display" />
    </Link>
  );
}

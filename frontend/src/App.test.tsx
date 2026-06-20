import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { SiteHeader } from "./components/site/SiteHeader";
import { SiteFooter } from "./components/site/SiteFooter";

vi.mock("@tanstack/react-router", () => ({
  Link: ({
    children,
    to,
    className,
  }: {
    children: React.ReactNode;
    to: string;
    className?: string;
  }) => (
    <a href={to} className={className}>
      {children}
    </a>
  ),
}));

describe("Frontend UI Components", () => {
  it("renders SiteHeader correctly with PyPI link", () => {
    render(<SiteHeader />);
    const linkElement = screen.getByRole("link", { name: /View on PyPI/i });
    expect(linkElement).toBeDefined();
    expect(linkElement.getAttribute("href")).toBe("https://pypi.org/project/contextly/");
  });

  it("renders SiteFooter correctly", () => {
    render(<SiteFooter />);
    const textElement = screen.getByText(/The operating system for AI/i);
    expect(textElement).toBeDefined();
  });
});

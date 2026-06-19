import { createFileRoute } from "@tanstack/react-router";
import { SiteHeader } from "@/components/site/SiteHeader";
import { SiteFooter } from "@/components/site/SiteFooter";

export const Route = createFileRoute("/docs")({
  component: Docs,
});

function Docs() {
  return (
    <div className="min-h-screen bg-[#FAFAFA] text-[#111111] font-sans antialiased selection:bg-[#111] selection:text-white">
      <SiteHeader />

      <main className="max-w-4xl mx-auto px-6 py-16">
        <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight mb-8">Documentation</h1>

        <div className="prose prose-neutral max-w-none prose-headings:font-bold prose-a:text-blue-600">
          <section className="mb-12">
            <h2 className="text-2xl font-bold mb-4">Introduction</h2>
            <p className="text-lg text-black/70 mb-4">
              <strong>Context-Ly CLI</strong> is an open-source Context Intelligence Engine designed
              to help developers generate high-quality, token-efficient context for Large Language
              Models (LLMs).
            </p>
            <p className="text-lg text-black/70">
              Rather than manually explaining your project to an AI assistant in every session,
              Context-Ly analyzes your repository, discovers conventions, learns team rules, and
              generates structured context files that help AI tools understand your codebase more
              effectively.
            </p>
          </section>

          <section className="mb-12">
            <h2 className="text-2xl font-bold mb-4 border-b pb-2">Installation</h2>
            <p className="mb-4 text-black/70">Install Context-Ly directly from PyPI:</p>
            <div className="bg-[#0A0A0A] text-white p-4 rounded-xl font-mono text-sm mb-4">
              pip install contextly
            </div>
            <p className="mb-4 text-black/70">Verify the installation:</p>
            <div className="bg-[#0A0A0A] text-white p-4 rounded-xl font-mono text-sm">
              contextly --help
            </div>
          </section>

          <section className="mb-12">
            <h2 className="text-2xl font-bold mb-6 border-b pb-2">Command Reference</h2>
            <div className="rounded-2xl border border-black/10 bg-white overflow-hidden shadow-sm">
              {[
                {
                  cmd: "init",
                  desc: "Initialize a .contextly environment in the current directory.",
                },
                { cmd: "discover", desc: "Run static analysis to find unwritten team patterns." },
                {
                  cmd: "learn --auto",
                  desc: "Interactively save discovered patterns to your rules memory.",
                },
                {
                  cmd: "analyze",
                  desc: "Build an ASCII architecture map of your entire repository.",
                },
                {
                  cmd: "pack <dir>",
                  desc: "Bundle code into a compressed, LLM-ready Context Pack.",
                },
                {
                  cmd: "export <pack>",
                  desc: "Fuse rules and packs into your clipboard instantly.",
                },
                { cmd: "inspect", desc: "Identify massive files that act as Token Hogs." },
                { cmd: "memory", desc: "View all rules permanently saved to project memory." },
                {
                  cmd: "explain <domain>",
                  desc: "Copy a structural context payload for a specific domain.",
                },
              ].map((c, i) => (
                <div
                  key={i}
                  className="group flex flex-col sm:flex-row sm:items-center border-b border-black/5 last:border-0 hover:bg-black/[0.02] transition-colors"
                >
                  <div className="sm:w-1/3 p-5 font-mono text-sm border-b sm:border-b-0 sm:border-r border-black/5 bg-black/[0.01] flex items-center justify-between">
                    <div>
                      <span className="text-black/40">contextly</span>{" "}
                      <span className="font-semibold">{c.cmd}</span>
                    </div>
                    <button
                      onClick={() => navigator.clipboard.writeText(`contextly ${c.cmd}`)}
                      className="opacity-0 group-hover:opacity-100 flex h-6 w-6 items-center justify-center rounded-md bg-black/5 text-black/40 hover:bg-black/10 hover:text-black transition-all focus:opacity-100"
                      title="Copy to clipboard"
                    >
                      <svg
                        width="12"
                        height="12"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      >
                        <rect width="14" height="14" x="8" y="8" rx="2" ry="2" />
                        <path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2" />
                      </svg>
                    </button>
                  </div>
                  <div className="sm:w-2/3 p-5 text-[15px] text-black/70">{c.desc}</div>
                </div>
              ))}
            </div>
          </section>
        </div>
      </main>

      <SiteFooter />
    </div>
  );
}

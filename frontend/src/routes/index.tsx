import { createFileRoute, Link } from "@tanstack/react-router";
import { useState } from "react";
import { SiteHeader } from "@/components/site/SiteHeader";
import { SiteFooter } from "@/components/site/SiteFooter";
import { Terminal, HardDrive, Cpu, Shield, ArrowRight } from "lucide-react";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Context-Ly | The Intelligence CLI for LLMs" },
      {
        name: "description",
        content:
          "A purpose-built CLI that automatically builds, compresses, and formats your codebase for any LLM.",
      },
    ],
  }),
  component: Landing,
});

function Landing() {
  return (
    <div className="min-h-screen bg-[#FAFAFA] text-[#111111] font-sans antialiased selection:bg-[#111] selection:text-white">
      <SiteHeader />

      <main>
        {/* Hero Section */}
        <section className="relative px-6 pt-12 pb-16 md:pt-16 md:pb-20 max-w-5xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 rounded-full border border-black/10 bg-white px-3 py-1 mb-6 shadow-sm">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
            </span>
            <span className="text-xs font-medium text-black/70 tracking-wide">
              v1.0.7 now available
            </span>
          </div>

          <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight text-balance leading-tight">
            The CLI for <br className="hidden md:block" /> LLM Context.
          </h1>

          <p className="mt-8 mx-auto max-w-2xl text-lg md:text-xl text-black/60 text-balance leading-relaxed">
            Stop dumping raw files into ChatGPT. Context-Ly automatically reads your codebase,
            discovers unwritten rules, and packages your project perfectly for any AI.
          </p>

          <div className="mt-12 flex flex-col sm:flex-row items-center justify-center gap-4">
            <div className="group relative flex items-center justify-between gap-4 rounded-xl border border-black/10 bg-white p-2 pl-5 pr-2 shadow-sm transition-all hover:shadow-md w-full sm:w-auto">
              <code className="font-mono text-sm text-black/80 select-all">
                $ pip install contextly
              </code>
              <button
                onClick={() => navigator.clipboard.writeText("pip install contextly")}
                className="flex h-8 w-8 items-center justify-center rounded-lg bg-black/5 text-black/40 hover:bg-black/10 hover:text-black transition-colors"
                title="Copy to clipboard"
              >
                <svg
                  width="14"
                  height="14"
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
            <a
              href="#how-to-use"
              className="inline-flex items-center gap-2 px-6 py-3.5 rounded-xl bg-black text-white font-medium text-sm hover:bg-black/80 transition-colors"
            >
              How it works <ArrowRight className="w-4 h-4" />
            </a>
          </div>
        </section>

        {/* Terminal Demo Section */}
        <section className="px-6 pb-24 max-w-5xl mx-auto">
          <div className="rounded-2xl border border-black/10 bg-[#0A0A0A] overflow-hidden shadow-2xl">
            <div className="flex items-center gap-2 px-4 py-3 border-b border-white/10 bg-white/5">
              <div className="flex gap-1.5">
                <div className="w-3 h-3 rounded-full bg-[#FF5F56]" />
                <div className="w-3 h-3 rounded-full bg-[#FFBD2E]" />
                <div className="w-3 h-3 rounded-full bg-[#27C93F]" />
              </div>
              <div className="ml-4 text-xs font-mono text-white/40">contextly pack</div>
            </div>
            <div className="p-6 font-mono text-sm overflow-x-auto text-white/80 leading-relaxed">
              <div className="flex gap-4">
                <span className="text-green-400">~/project</span>
                <span className="text-white">$ contextly pack .</span>
              </div>
              <div className="mt-4 text-blue-400">Context-Ly Engine v1.0.7</div>
              <div className="mt-2 text-white/50">Analyzing 1,420 files...</div>
              <div className="mt-1 text-white/50">Applying AST compression...</div>
              <div className="mt-1 text-white/50">Writing fenced Markdown context...</div>

              <div className="mt-4 text-white">
                <span className="text-green-400">✔</span> Context pack generated successfully.
              </div>
              <div className="mt-4 grid grid-cols-2 gap-4 max-w-sm text-xs">
                <div>
                  <div className="text-white/40 uppercase tracking-widest">Original Tokens</div>
                  <div className="mt-1 text-red-400">842,000</div>
                </div>
                <div>
                  <div className="text-white/40 uppercase tracking-widest">Packed Tokens</div>
                  <div className="mt-1 text-green-400">114,000 (-86%)</div>
                </div>
              </div>
              <div className="mt-6 flex gap-4">
                <span className="text-green-400">~/project</span>
                <span className="text-white/50 animate-pulse">_</span>
              </div>
            </div>
          </div>
        </section>

        {/* Core Architecture */}
        <section className="border-t border-black/5 bg-white py-24 px-6">
          <div className="max-w-5xl mx-auto">
            <div className="mb-16">
              <h2 className="text-3xl font-bold tracking-tight">Purpose-built for LLMs.</h2>
              <p className="mt-4 text-black/60 max-w-2xl text-lg">
                Generic scripts copy-paste your node_modules. Context-Ly uses AST-aware parsing to
                generate high-signal, token-efficient prompt payloads.
              </p>
            </div>

            <div className="grid md:grid-cols-2 gap-x-12 gap-y-16">
              {[
                {
                  icon: <Cpu className="w-5 h-5" />,
                  title: "AST Compression",
                  desc: "Removes dead code, empty lines, and redundant comments while preserving structural syntax for LLMs.",
                },
                {
                  icon: <HardDrive className="w-5 h-5" />,
                  title: "O(1) Memory Streaming",
                  desc: "Handles gigabyte-scale monorepos without crashing your machine by streaming files to disk.",
                },
                {
                  icon: <Terminal className="w-5 h-5" />,
                  title: "Pattern Discovery",
                  desc: "Automatically infers your tech stack and unwritten architectural rules, saving them to a local memory store.",
                },
                {
                  icon: <Shield className="w-5 h-5" />,
                  title: "Structured Markdown Packs",
                  desc: "Wraps source files in readable fenced Markdown sections that preserve filenames, languages, and context boundaries.",
                },
              ].map((feature, i) => (
                <div key={i} className="relative">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-black/5 border border-black/10 text-black mb-5">
                    {feature.icon}
                  </div>
                  <h3 className="text-xl font-bold tracking-tight mb-3">{feature.title}</h3>
                  <p className="text-black/60 leading-relaxed">{feature.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <HowToUse />
      </main>

      <SiteFooter />
    </div>
  );
}

const COMMANDS = [
  {
    name: "init",
    description:
      "Initializes Context-as-Code in the current directory. It creates a `.contextly` directory containing configuration files to tailor the engine's behavior to your project's specific needs.",
    usage: "$ contextly init",
    output: `[OK] Initialized Contextly in .contextly/
[OK] Created default config.yaml
[OK] You are ready to analyze and pack!`,
  },
  {
    name: "analyze",
    description:
      "Automatically analyzes and maps the repository. It scans your codebase, parsing ASTs to build a comprehensive graph of your entities, functions, and classes.",
    usage: "$ contextly analyze",
    output: `[OK] Starting repository analysis...
[OK] Parsed 179 files
[OK] Extracted 1,302 entities and 2,976 edges
[OK] Graph saved to .contextly/memory/graph.json`,
  },
  {
    name: "discover",
    description:
      "Statically analyzes the repository to discover conventions. It detects your build tools, frameworks, languages, and architectural patterns, generating a PROJECT_CONTEXT.md file.",
    usage: "$ contextly discover",
    output: `[OK] Pattern Discovery Complete:

Build Tool:
  [OK] Vite (High Confidence) - Uses Vite as the frontend build tool.

Frontend Framework:
  [OK] React (High Confidence) - Uses React for building user interfaces.

Language:
  [OK] TypeScript (High Confidence) - Uses TypeScript for type-safe JavaScript.

Generated advanced PROJECT_CONTEXT.md (chatgpt format) in current directory.`,
  },
  {
    name: "stats",
    description:
      "Generates an enterprise repository health report. It gives you a detailed overview of graph topology, resolution quality, and architectural hotspots.",
    usage: "$ contextly stats",
    output: `+---------------------------------------+
| Contextly Repository Health Report: . |
+---------------------------------------+

[ Repository Health Score: 83.7/100 ]

[ Graph Topology ]
• Files Analyzed:       179
• Entities Discovered:  1302

[ Architectural Hotspots (Top 3) ]
• Most Connected:
  1. str                  (93 edges)
  2. runner.invoke        (92 edges)
  3. PackerEngine         (80 edges)`,
  },
  {
    name: "pack",
    description:
      "Bundles a directory into an LLM-ready Context Pack. It combines the graph intelligence and compressed source code into a highly optimized Markdown file.",
    usage: "$ contextly pack",
    output: `[OK] Context Pack 'Contextly' created!

                             Pack Summary                              
                     Source  '.'                                       
               Files Packed  194                                       
 Exact Tokens (cl100k_base)  16,873                                    
            Output Location  .contextly\\packs\\Contextly.contextpack.md`,
  },
];

function HowToUse() {
  const [activeCommand, setActiveCommand] = useState(0);

  return (
    <section id="how-to-use" className="bg-[#0A0A0A] py-24 px-6 border-t border-white/10">
      <div className="max-w-5xl mx-auto">
        <div className="mb-16 text-center">
          <h2 className="text-3xl font-bold tracking-tight text-white">How to use</h2>
          <p className="mt-4 text-white/60 max-w-2xl mx-auto text-lg">
            Context-Ly provides a suite of tools to analyze, map, and package your repository for
            LLMs. Here is a detailed breakdown of every command.
          </p>
        </div>

        <div className="grid lg:grid-cols-12 gap-8 items-start">
          {/* Tabs */}
          <div className="lg:col-span-4 flex flex-col gap-2">
            {COMMANDS.map((cmd, idx) => (
              <button
                key={cmd.name}
                onClick={() => setActiveCommand(idx)}
                className={`text-left px-5 py-4 rounded-xl border transition-all ${
                  activeCommand === idx
                    ? "bg-white/10 border-white/20 text-white shadow-sm"
                    : "bg-transparent border-transparent text-white/50 hover:bg-white/5 hover:text-white/80"
                }`}
              >
                <div className="font-mono text-sm font-semibold mb-1">contextly {cmd.name}</div>
                <div className="text-xs line-clamp-2 leading-relaxed opacity-80">
                  {cmd.description}
                </div>
              </button>
            ))}
          </div>

          {/* Terminal View */}
          <div className="lg:col-span-8">
            <div className="rounded-2xl border border-white/10 bg-black overflow-hidden shadow-2xl relative">
              <div className="flex items-center gap-2 px-4 py-3 border-b border-white/10 bg-white/5">
                <div className="flex gap-1.5">
                  <div className="w-3 h-3 rounded-full bg-[#FF5F56]" />
                  <div className="w-3 h-3 rounded-full bg-[#FFBD2E]" />
                  <div className="w-3 h-3 rounded-full bg-[#27C93F]" />
                </div>
                <div className="ml-4 text-xs font-mono text-white/40">
                  contextly {COMMANDS[activeCommand].name}
                </div>
              </div>
              <div className="p-6 font-mono text-sm overflow-x-auto text-white/80 leading-relaxed min-h-[320px]">
                <div className="flex gap-4 mb-6">
                  <span className="text-green-400">~/project</span>
                  <span className="text-white">{COMMANDS[activeCommand].usage}</span>
                </div>
                <pre className="text-white/70 whitespace-pre-wrap font-mono text-sm">
                  {COMMANDS[activeCommand].output}
                </pre>
                <div className="mt-6 flex gap-4">
                  <span className="text-green-400">~/project</span>
                  <span className="text-white/50 animate-pulse">_</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

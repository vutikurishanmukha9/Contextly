import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { SiteHeader } from "@/components/site/SiteHeader";
import { SiteFooter } from "@/components/site/SiteFooter";
import { Terminal, HardDrive, Cpu, Shield, ArrowRight, FileCode, CheckCircle2 } from "lucide-react";
import * as Tabs from "@radix-ui/react-tabs";
import { toast } from "sonner";

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
              v1.1.0 now available
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
                onClick={async () => {
                  try {
                    await navigator.clipboard.writeText("pip install contextly");
                    toast.success("Copied to clipboard!");
                  } catch (err) {
                    toast.error("Failed to copy command");
                  }
                }}
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
                <span className="text-white">$ contextly pack --task "authentication flow" .</span>
              </div>
              <div className="mt-4 text-blue-400">Context-Ly Engine v1.1.0</div>
              <div className="mt-2 text-white/50">Analyzing 1,420 files...</div>
              <div className="mt-1 text-white/50">Building graph for task relevance...</div>
              <div className="mt-1 text-white/50">Applying AST compression...</div>

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
    shortDesc: "Initializes Context-as-Code in the current directory.",
    fullDesc:
      "Sets up the foundation for Context-Ly by creating the necessary configuration and memory directories in your project root.",
    generates: {
      file: ".contextly/config.yaml",
      content:
        "A customizable YAML configuration file that defines ignore patterns, include rules, and engine settings specific to your repository.",
    },
    usage: "$ contextly init",
    output: `[OK] Initialized Contextly in .contextly/
[OK] Created default config.yaml
[OK] You are ready to analyze and pack!`,
  },
  {
    name: "analyze",
    shortDesc: "Scans and maps the entire repository.",
    fullDesc:
      "Performs a deep AST-level parse of your entire codebase to extract all classes, functions, and their intricate dependencies.",
    generates: {
      file: ".contextly/memory/graph.json",
      content:
        "A structured JSON graph of your codebase's architecture, tracking how every entity relates to one another.",
    },
    usage: "$ contextly analyze",
    output: `[OK] Starting repository analysis...
[OK] Parsed 179 files
[OK] Extracted 1,302 entities and 2,976 edges
[OK] Graph saved to .contextly/memory/graph.json`,
  },
  {
    name: "discover",
    shortDesc: "Statically analyzes the repository to discover conventions.",
    fullDesc:
      "Automatically infers your tech stack, frameworks, and architectural design patterns without you having to write a single line of documentation.",
    generates: {
      file: "PROJECT_CONTEXT.md",
      content:
        "A high-level markdown intelligence briefing detailing your project's primary languages, build tools, state management, and architectural topology.",
    },
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
    name: "learn --auto",
    shortDesc: "Converts discovered conventions into permanent project memory.",
    fullDesc:
      "Automatically saves all discovered architectural patterns, frameworks, and conventions into your project's .contextly/memory/rules.yaml.",
    generates: {
      file: ".contextly/memory/rules.yaml",
      content: "Persistent memory layer of team rules and architectural conventions.",
    },
    usage: "$ contextly learn --auto",
    output: `START

Discovered Conventions:

[OK] Successfully saved 10 rules to persistent memory!
Run contextly memory to view them.`,
  },
  {
    name: "memory",
    shortDesc: "Inspects all stored project memory and conventions.",
    fullDesc:
      "Displays all saved rules, conventions, and architectural preferences currently remembered by Context-Ly.",
    generates: {
      file: "Terminal (stdout)",
      content: "Outputs the currently saved memory rules directly to your terminal screen.",
    },
    usage: "$ contextly memory",
    output: `START
Stored Memory (Found 10 rules)

Architecture Hints
  - [rule_1ecd239a] Found directory structure indicating Service Layer.

Build Tool
  - [rule_1241fdad] Uses Vite as the frontend build tool.`,
  },
  {
    name: "pack",
    shortDesc: "Bundles a directory into an LLM-ready Context Pack.",
    fullDesc:
      "The core engine command. It fuses the graph intelligence, unwritten rules, and AST-compressed source code into a single, highly optimized token-efficient payload.",
    generates: {
      file: ".contextly/packs/<name>.contextpack.md",
      content:
        "A massive, perfectly formatted markdown file containing your structured codebase, ready to be attached to ChatGPT, Claude, or any LLM.",
    },
    usage: '$ contextly pack --task "authentication flow"',
    output: `[OK] Context Pack 'authentication_flow' created!

                             Pack Summary                              
                     Source  '.'                                       
               Files Packed  20                                        
 Exact Tokens (cl100k_base)  1,119                                     
            Output Location  .contextly\\packs\\authentication_flow.contextpack.md`,
  },
  {
    name: "inspect",
    shortDesc: "Analyzes repository complexity and token consumption.",
    fullDesc:
      "Provides visibility into large files and potential token-heavy directories that may negatively impact AI context quality.",
    generates: {
      file: "Terminal (stdout)",
      content: "Outputs the token hogs and complexity metrics directly to the terminal.",
    },
    usage: "$ contextly inspect",
    output: `START

[OK] Inspection complete!

               Top 5 Largest Files (Potential Token Hogs)                
+-----------------------------------------------------------------------+
| Size (KB) | File Path                                                 |
+-----------------------------------------------------------------------+`,
  },
  {
    name: "export",
    shortDesc: "Fuses memory rules and a pack into a Context Payload.",
    fullDesc:
      "Combines your persistent project memory with a specific context pack, instantly copying the optimized payload to your clipboard for LLM usage.",
    generates: {
      file: ".contextly/exports/export_<name>_<date>.md",
      content: "A unified payload ready to be pasted directly into an LLM.",
    },
    usage: "$ contextly export cli",
    output: `START

[OK] Export Generation Complete!
  - Intelligence: PROJECT_CONTEXT.md
  - Context Pack: cli

Successfully copied to clipboard!`,
  },
  {
    name: "explain",
    shortDesc: "Extracts a structural context payload for a specific domain.",
    fullDesc:
      "Generates a highly-optimized structural context based on the AST Knowledge Graph, helping the LLM understand architecture without raw files.",
    generates: {
      file: ".contextly/exports/contextly explain <domain>_result.md",
      content: "A domain-specific structural JSON payload.",
    },
    usage: "$ contextly explain core",
    output: `START
[OK] Context payload saved to: 
.contextly\\exports\\contextly explain core\\contextly explain core_result.md
Notice: Proprietary source architecture has also been copied to your OS clipboard.`,
  },
  {
    name: "stats",
    shortDesc: "Generates an enterprise repository health report.",
    fullDesc:
      "Provides a deep dive into your repository's complexity, identifying your most depended-upon files, orphaned code, and structural hotspots.",
    generates: {
      file: "Terminal (stdout)",
      content: "Outputs the comprehensive health report and diagnostics directly to the terminal.",
    },
    usage: "$ contextly stats",
    output: `+---------------------------------------+
| Contextly Repository Health Report: . |
+---------------------------------------+

[ Repository Health Score: 75.0/100 ]
  -15.0 points for 82 potential orphans
  -10.0 points for 1099 unresolved external symbols

[ Graph Topology ]
• Files Analyzed:       205
• Entities Discovered:  1619

[ Architectural Hotspots (Top 3) ]
• Most Connected:
  1. runner.invoke        (Hub Score: 224)
  2. PackerEngine         (Hub Score: 136)

[ Module Coupling (Top 3 Unstable) ]

[ Maintainability ]
• Avg Functions per File: 1.8
• Fat Modules (Top 3):
  1. models               (20 internal entities)`,
  },
  {
    name: "impact <file>",
    shortDesc: "Calculates the blast radius of a given file.",
    fullDesc:
      "Analyzes the AST graph to find all downstream files that depend on the target file, assigning a risk level.",
    generates: {
      file: "Terminal (stdout)",
      content: "Outputs the blast radius and risk level directly to the terminal.",
    },
    usage: "$ contextly impact cli/contextly/utils/fs.py",
    output: `START

Blast Radius

Files Affected: 17

Risk:
HIGH

Most Critical Dependents:
- analyze
- discover
- pack
- export`,
  },
  {
    name: "summary",
    shortDesc: "Provides a high-level overview of the repository scale.",
    fullDesc:
      "Analyzes the graph to detect core hubs, executable entry points, and primary domains within the codebase.",
    generates: {
      file: "Terminal (stdout)",
      content: "Outputs a concise architectural summary of the repository.",
    },
    usage: "$ contextly summary",
    output: `START

Repository Summary (Contextly)

+--------- Scale ---------+
|  Total Files:      206  |
|  Total Classes:    97   |
|  Total Functions:  369  |
+-------------------------+

Primary Domains / Modules:
  - cli/contextly
  - cli/tests
  - frontend/src

Core Hubs (Most Depended-Upon Files):
  - frontend/src/lib/utils.ts (43 incoming imports)
  - cli/contextly/utils/exceptions.py (20 incoming imports)`,
  },
];

function HowToUse() {
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

        <div className="flex flex-col gap-24 mt-16 max-w-4xl mx-auto">
          {COMMANDS.map((cmd, index) => (
            <div key={cmd.name} className="flex flex-col gap-6 relative">
              {index > 0 && <div className="absolute -top-12 left-0 right-0 h-px bg-white/5" />}

              <div className="bg-white/5 border border-white/10 rounded-2xl p-6 md:p-8">
                <h3 className="text-2xl font-bold text-white mb-3">contextly {cmd.name}</h3>
                <p className="text-white/70 text-lg leading-relaxed mb-6">{cmd.fullDesc}</p>

                {cmd.generates && (
                  <div className="bg-white/[0.03] border border-white/10 rounded-xl p-5 shadow-inner">
                    <div className="flex items-center gap-2 mb-3">
                      {cmd.generates.file === "Terminal (stdout)" ? (
                        <Terminal className="w-4 h-4 text-[#FFBD2E]" />
                      ) : (
                        <FileCode className="w-4 h-4 text-[#27C93F]" />
                      )}
                      <span className="text-sm font-semibold tracking-wide text-white uppercase opacity-90">
                        Output Location
                      </span>
                    </div>
                    <div className="pl-6 border-l border-white/10 ml-2">
                      <div
                        className={`font-mono text-sm mb-2 inline-block px-2 py-0.5 rounded ${cmd.generates.file === "Terminal (stdout)" ? "text-[#FFBD2E] bg-[#FFBD2E]/10" : "text-[#27C93F] bg-[#27C93F]/10"}`}
                      >
                        {cmd.generates.file}
                      </div>
                      <p className="text-sm text-white/60 leading-relaxed">
                        {cmd.generates.content}
                      </p>
                    </div>
                  </div>
                )}
              </div>

              <div className="rounded-2xl border border-white/10 bg-black overflow-hidden shadow-2xl relative">
                <div className="flex items-center gap-2 px-4 py-3 border-b border-white/10 bg-white/5">
                  <div className="flex gap-1.5">
                    <div className="w-3 h-3 rounded-full bg-[#FF5F56]" />
                    <div className="w-3 h-3 rounded-full bg-[#FFBD2E]" />
                    <div className="w-3 h-3 rounded-full bg-[#27C93F]" />
                  </div>
                  <div className="ml-4 text-xs font-mono text-white/40">Terminal Output</div>
                </div>
                <div className="p-6 font-mono text-sm overflow-x-auto text-white/80 leading-relaxed min-h-[280px]">
                  <div className="flex gap-4 mb-6">
                    <span className="text-green-400">~/project</span>
                    <span className="text-white">{cmd.usage}</span>
                  </div>
                  <pre className="text-white/70 whitespace-pre-wrap font-mono text-sm">
                    {cmd.output}
                  </pre>
                  <div className="mt-6 flex gap-4">
                    <span className="text-green-400">~/project</span>
                    <span className="text-white/50 animate-pulse">_</span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

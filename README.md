# Context-Ly

[![PyPI version](https://img.shields.io/pypi/v/contextly.svg)](https://pypi.org/project/contextly/)
[![Python Version](https://img.shields.io/pypi/pyversions/contextly.svg)](https://pypi.org/project/contextly/)
[![Test Suite](https://img.shields.io/badge/tests-328%20passed-success)](https://github.com/vutikurishanmukha9/Contextly)
[![Coverage](https://img.shields.io/badge/coverage-90.54%25-brightgreen)](https://github.com/vutikurishanmukha9/Contextly)
[![Security Status](https://img.shields.io/badge/security-0%20vulnerabilities-brightgreen)](https://github.com/vutikurishanmukha9/Contextly)
[![License](https://img.shields.io/badge/license-Proprietary-blue)](LICENSE)

> **The Ultimate Context-as-Code & Context Intelligence Engine for LLMs**  
> Build context once. Eliminate hallucinations. Supercharge Claude 3.7, ChatGPT o3, DeepSeek, and Gemini with surgical repository intelligence.

---

## Why Context-Ly?

Modern AI coding assistants are only as good as the context you feed them. Dumping entire codebases into an LLM wastes thousands of tokens, blows through context windows, and drowns the model in irrelevant boilerplate. Explaining your codebase by hand in every new chat prompt is tedious and inconsistent.

**Context-Ly solves this forever.** It turns your codebase into a living **Context Memory Layer**:
- **Extracts Deep Structural Knowledge**: Uses native AST parsing and knowledge graph clustering to understand imports, call trees, and core architecture hubs.
- **1-Step Prompt Synthesis**: Packs code and automatically fuses high-level repository context directly into your clipboard—ready to paste in 1 step.
- **Pinpoint Blast Radius**: Calculates the exact downstream impact of modifying any file before you write code.
- **Persistent Team Memory**: Discovers, learns, and remembers your team's coding conventions and architectural rules across sessions.
- **Security Hardened**: Zero telemetry, prompt-injection resistant delimiters, and automated clipboard isolation for CI.

---

## Installation

Install Context-Ly directly via `pip` or `uv`:

```bash
# Using pip
pip install contextly

# Using uv
uv tool install contextly
```

Verify your installation:

```bash
contextly --help
```

---

## Quick Start (in 30 Seconds)

Get up and running in any project with 3 commands:

```bash
# 1. Initialize Context-as-Code with auto-detected tech stack profiles
contextly init --quick

# 2. Analyze repository architecture & generate PROJECT_CONTEXT.md
contextly analyze

# 3. Pack your target code & automatically fuse intelligence to clipboard
contextly pack src/components
```

**Done!** Your clipboard now contains a synthesized, token-optimized context prompt complete with architecture maps, team conventions, and target source code—ready to paste directly into ChatGPT, Claude, or any LLM.

---

## The 5 Core Powerhouse Commands

Context-Ly consolidates repository intelligence into **5 powerhouse commands**:

```text
Usage: contextly [OPTIONS] COMMAND [ARGS]...

Context Intelligence Engine for LLMs

+- Commands ------------------------------------------------------------------+
| init      Initialize Context-as-Code with auto-detected stack profiles      |
| analyze   Analyze architecture, health scorecard, hubs, and complexity      |
| pack      Bundle, optimize, and fuse repository context for instant LLM     |
|           export                                                            |
| impact    Analyze blast radius of modifying a target file or explain domain |
|           architecture                                                      |
| memory    Inspect, learn, and discover persistently stored team conventions |
+-----------------------------------------------------------------------------+
```

---

### 1. `contextly init` — Smart Context-as-Code Setup

Initializes Context-Ly in your repository with automatic framework detection and tailored packing profiles.

```bash
# Interactive guided setup
contextly init

# Non-interactive instant setup (perfect for CI or scripts)
contextly init --quick

# Force re-initialization
contextly init --force
```

**Key Features:**
- **Stack & Framework Detection**: Automatically detects React, Next.js, Vue, FastAPI, Flask, Django, Express, Go, Rust, and Python.
- **Smart Profiles**: Automatically configures `.contextly/config.yaml` with workspace profiles (e.g., `frontend`, `backend`, `api`).

---

### 2. `contextly analyze` — Unified Architecture & Health Intelligence

Analyzes repository structure, dependencies, and architectural complexity. Subsumes `summary`, `stats`, and `inspect`.

```bash
# Standard analysis: Generates PROJECT_CONTEXT.md and intelligence summary
contextly analyze

# High-level human-readable architecture summary & entry points
contextly analyze --summary

# Enterprise repository health scorecard, modularity, & hub hotspots
contextly analyze --stats

# Deep AST inspection, complexity hotspots, & token consumption
contextly analyze --inspect

# Target-specific formatting for Claude XML or ChatGPT Markdown
contextly analyze --model claude
contextly analyze --model chatgpt
```

**Generated Artifacts:**
- `PROJECT_CONTEXT.md`: An AI-optimized architecture document detailing technologies, entry points, core abstractions, and conventions.

---

### 3. `contextly pack` — 1-Step Prompt & Intelligence Fusion

Bundles a target directory into an LLM-ready Context Pack and automatically synthesizes high-level architectural intelligence. Subsumes `export`.

```bash
# Pack a directory with automatic PROJECT_CONTEXT.md clipboard fusion
contextly pack src/auth --name auth-module

# Pack without fusing the architecture layer (raw code pack only)
contextly pack src/auth --standalone

# Pack using a pre-configured profile from .contextly/config.yaml
contextly pack --profile frontend

# Task-focused packing: drops least relevant files to fit token budget
contextly pack src/ --task "refactor payment webhooks" --max-tokens 32000

# Export as an environment variable script for CI/terminal pipelines
contextly pack src/auth --env
```

**Intelligence Fusion:**
By default, `pack` fuses the repository intelligence layer with the target code pack in memory and copies the complete prompt to your clipboard with zero manual export steps.

---

### 4. `contextly impact` — Blast Radius & Domain Intelligence

Calculates the ripple effect of changing a file before modifying it. Subsumes `explain`.

```bash
# Compute blast radius risk for a file
contextly impact src/core/engine.py

# Render a hierarchical visual cascade tree diagram
contextly impact src/core/engine.py --visual

# Explain a domain's architecture and entry points
contextly impact auth --explain

# Run without copying to clipboard (CI / privacy)
contextly impact src/core/engine.py --no-clipboard
```

**Visual Cascade Tree Example:**

```text
* src/core/engine.py (Modified Target)
  ├── [HIGH] src/api/routes.py
  ├── [HIGH] src/services/worker.py
  ├── ... and 2 more HIGH risk files
  ├── [MEDIUM] src/models/schema.py
  ├── ... and 3 more MEDIUM risk files
  └── [LOW] tests/test_engine.py
```

---

### 5. `contextly memory` — Team Memory & Knowledge Vault

Maintains persistent team conventions, architectural rules, and coding standards. Subsumes `learn` and `discover`.

```bash
# View all stored team conventions grouped by category
contextly memory

# Teach a custom convention
contextly memory --learn "All database queries must use async session context" --category "Database"

# Automatically discover emergent conventions from the codebase
contextly memory --auto

# Non-interactively accept and persist all discovered conventions
contextly memory --auto --apply-all

# Delete a convention by ID
contextly memory --delete c4a89f

# Clear the memory vault
contextly memory --clear
```

**Persistent Vault:**
Conventions are stored in version-controlled `.contextly/memory/rules.yaml`, ensuring that every team member and AI assistant follows identical guidelines.

---

## Backward Compatibility Matrix

All 7 legacy commands remain active as hidden aliases (`hidden=True`). Existing scripts and workflows continue to work without breaking:

| Legacy Command | Modern Equivalent | Status |
| :--- | :--- | :--- |
| `contextly export <pack>` | `contextly pack` *(automatic fusion)* | Active Alias |
| `contextly stats` | `contextly analyze --stats` | Active Alias |
| `contextly summary` | `contextly analyze --summary` | Active Alias |
| `contextly inspect` | `contextly analyze --inspect` | Active Alias |
| `contextly explain <domain>` | `contextly impact <domain> --explain` | Active Alias |
| `contextly learn` | `contextly memory --auto` / `--learn` | Active Alias |
| `contextly discover` | `contextly memory --auto` | Active Alias |

---

## Security & Privacy by Design

Context-Ly is built for enterprise engineering environments:

- **100% Local Execution**: All AST parsing, graph building, and analysis run locally on your CPU. No source code or telemetry is ever transmitted over the network.
- **Prompt Injection Defense**: Encapsulates context layers and escapes closing tags (`</context_pack>` -> `&lt;/context_pack&gt;`) to prevent prompt boundary escaping attacks.
- **Clipboard Isolation**: All clipboard operations respect the `--no-clipboard` flag and automatically disable clipboard access when running in CI environments (`CI=true`).
- **Zero Vulnerabilities**: 100% clean security audit with zero known package vulnerabilities.

---

## Ignore Philosophy

Context-Ly respects distinct ignore policies depending on the operation:
1. **Packing & Inspection (`pack`, `analyze --inspect`)**: Strictly obeys `.gitignore` and `.contextlyignore` to prevent bundling `node_modules`, build artifacts, and vendor files into your prompt budget.
2. **Architecture & Memory Discovery (`analyze`, `memory --auto`)**: Bypasses `.gitignore` for monorepo subpackages (e.g. `frontend/`) while enforcing minimal skip-lists (`.git`, `.venv`), ensuring valid application architecture is never missed.

---

## Tech Stack & Requirements

- **Python**: `>= 3.9`
- **CLI Framework**: Typer & Rich
- **AST Parsing**: Tree-Sitter & Python `ast`
- **Graph Engine**: Knowledge Graph with reverse adjacency traversal
- **Packaging**: Setuptools & PyPI

---

## License

This project is proprietary and distributed under the Contextly End-User License Agreement (EULA). See the [LICENSE](LICENSE) file for details.

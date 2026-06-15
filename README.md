# Context-Ly CLI

**Context-Ly CLI** is an open-source Context Intelligence Engine designed to help developers generate high-quality, token-efficient context for Large Language Models (LLMs).

Rather than manually explaining your project to an AI assistant in every session, Context-Ly analyzes your repository, discovers conventions, learns team rules, and generates structured context files that help AI tools understand your codebase more effectively.

The CLI acts as a persistent **Context Memory Layer** for your repository, enabling consistent AI interactions across development workflows.

---

## Features

* **Offline Context Generation**: Context-Ly operates entirely offline, keeping your code secure and saving LLM tokens.
* **Architecture Visualization & Domain Clustering**: Automatically segments code into coherent architectural domains (`core`, `shared`, etc.).
* **Automatic Framework & Dependency Detection**: Discovers project stack, languages, and dependencies instantly.
* **Team Convention Discovery**: Statically analyzes the repository to learn unwritten coding conventions and state management preferences.
* **Persistent Context Storage**: Stores project memory locally (`.contextly/config.yaml`), allowing "Context-as-Code" via version control.
* **LLM-ready Context Packs**: Bundles specific directories into optimized Markdown context files for LLMs.
* **Zero Token Waste**: Features like `contextly explain <domain>` extract structural JSON payloads without streaming raw LLM responses.
* **Clipboard-First Workflow**: Seamlessly pushes generated context packs directly to the clipboard for immediate use.
* **Enterprise-Scale Stability**: Deterministic output generation and built-in binary immunity to prevent AST parsing crashes.

---

## Installation

Install Context-Ly directly from PyPI:

```bash
pip install contextly
```

Verify the installation:

```bash
contextly --help
```

---

## Prerequisites

* Python 3.9 or later
* A local Git repository or project directory to analyze

No external services or API keys are required for the core functionality.

---

## Quick Start

Initialize Context-Ly in your project:

```bash
contextly init
```

Analyze your repository and generate a complete project context:

```bash
contextly analyze
```

This command automatically:

* Reads your README documentation
* Scans the project structure
* Detects frameworks and dependencies
* Discovers conventions and stored memory
* Generates a comprehensive `PROJECT_CONTEXT.md`

The generated file can be used directly with AI coding assistants and LLMs.

---

## Commands

### `contextly init`

Initialize Context-Ly in the current project.

```bash
contextly init
```

Creates:

```text
.contextly/
├── config.yaml
├── memory/
└── packs/
```

---

### `contextly analyze`

Generate a complete repository context file.

```bash
contextly analyze
```

This command:

* Reads project documentation
* Analyzes repository structure
* Detects frameworks and technologies
* Loads stored team conventions
* Generates `PROJECT_CONTEXT.md`

Output:

```text
PROJECT_CONTEXT.md
```

---

### `contextly discover`

Run the Pattern Discovery Engine.

```bash
contextly discover
```

Discovers repository conventions such as:

* TailwindCSS usage
* Zustand state management
* React Query patterns
* Service-layer architecture hints
* Framework-specific conventions

The command provides insight into patterns already present within the codebase.

---

### `contextly learn --auto`

Convert discovered conventions into permanent project memory.

```bash
contextly learn --auto
```

Example:

```text
Save convention: TailwindCSS (Uses TailwindCSS for styling.)? [y/N]
```

Approved conventions are stored in:

```text
.contextly/memory/rules.yaml
```

This creates a persistent memory layer that can be committed to source control and shared across teams.

---

### `contextly memory`

Inspect all stored project memory and conventions.

```bash
contextly memory
```

Displays all saved rules, conventions, and architectural preferences currently remembered by Context-Ly.

---

### `contextly pack <directory>`

Generate an LLM-ready Context Pack from a specific directory.

```bash
contextly pack src/components
```

The command:

* Reads all files in the target directory
* Calculates token usage
* Bundles the content into a reusable Context Pack

Output location:

```text
.contextly/packs/
```

Useful for sharing focused portions of a large codebase with an LLM.

---

### `contextly inspect`

Analyze repository complexity and token consumption.

```bash
contextly inspect
```

Provides visibility into:

* Large files
* Potential token-heavy directories
* Context window bottlenecks
* Repository complexity hotspots

This helps identify areas that may negatively impact AI context quality.

---

### `contextly export <pack_name>`

Fuses your memory rules and the specified context pack into a single, comprehensive Context Payload.

```bash
contextly export cli
```

The output is instantly copied to your clipboard, ready to be pasted directly into an LLM.

---

### `contextly explain <domain>`

Extracts a highly-optimized structural context payload for a specific domain based on the AST Knowledge Graph.

```bash
contextly explain core
```

It copies a JSON payload to your clipboard, allowing the LLM to understand the architecture without wasting tokens scanning raw files.

---

### Understanding Context-Ly Ignore Philosophies

Context-Ly utilizes two distinct "ignore" policies depending on the operation:

1. **Packing & Inspection (`contextly pack`, `contextly inspect`)**: These commands **respect** your `.gitignore` and `.contextlyignore` files. This ensures that generated packs and token counts omit irrelevant files (like `node_modules`, compiled binaries, etc.), producing concise, token-efficient context for the LLM.
2. **Discovery & Intelligence (`contextly discover`, `contextly learn`)**: The Pattern Discovery Engine **ignores** your `.gitignore`. It uses a minimal, hardcoded skip-list (only completely toxic directories like `.git` or `.venv`). This allows Context-Ly to correctly discover architectural patterns and package dependencies in valid directories (like a `frontend/` folder) that you might have legitimately added to `.gitignore` to keep your root repository clean.

---

## Example Workflow

```bash
contextly init

contextly discover

contextly learn --auto

contextly analyze
```

Result:

```text
.contextly/
PROJECT_CONTEXT.md
```

Your repository now has a persistent memory layer and an AI-ready context file generated from both repository analysis and learned team conventions.

---

## Why Context-Ly?

Modern AI coding tools are powerful, but they often lack project-specific context.

Context-Ly bridges that gap by transforming repository knowledge, team conventions, and architectural patterns into structured context that can be consistently shared with LLMs.

The goal is simple:

**Build context once. Use it everywhere.**

---

## Changelog

For all release notes and version history, please see the [CHANGELOG.md](https://github.com/vutikurishanmukha9/Contextly/blob/main/cli/CHANGELOG.md).

---

## Contributing

Contributions, issues, and feature requests are welcome.

If you discover a bug, have an idea for improving repository intelligence, or want to contribute new scanners and analysis capabilities, please open an issue or submit a pull request.

---

## License

This project is open source and distributed under the terms of its license.

See the LICENSE file for details.

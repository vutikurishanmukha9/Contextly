# Context-Ly

**Imagine trying to hire a new employee, but instead of giving them an employee handbook, a map of the office, and a list of company rules, you just dump 10,000 loose papers on their desk and say, "figure it out."** 

That is how most people use AI today. They dump raw files into ChatGPT or Claude and hope for the best. The AI gets confused, makes mistakes, and wastes time.

**Context-Ly fixes this.** 

Context-Ly is a tool that automatically reads your project, figures out your unwritten rules, maps out how everything is connected, and packages it perfectly for AI. When you use Context-Ly, the AI instantly understands your project exactly like a senior engineer would—saving you hours of typing, explaining, and correcting.

---

## Overview

Modern AI applications often suffer from "token waste" - providing either too little context (requiring repeated clarifications) or too much irrelevant context (diluting the model's focus). Context-Ly solves this by introducing a structured methodology for building context packs. 

The application sits between the user's raw thoughts and the AI model, enforcing best practices in prompt engineering through an intuitive interface and a real-time heuristic scoring engine.

## Core Features

### 1. Context Builder
The Context Builder allows users to break down their prompts into distinct, manageable blocks:
- **Goal**: The primary objective or task (What does success look like?).
- **Background**: Necessary prerequisite information for the model.
- **Constraints**: Strict boundaries, desired tone, and format restrictions.
- **Examples**: Few-shot examples, gold standards, or anti-examples to guide the model.
- **Files**: Supporting reference materials such as code snippets or documentation.

### 2. Real-Time Context Scoring
Every context pack is graded algorithmically before it touches an LLM. The scoring engine evaluates the context across four axes:
- **Relevance**: Analyzes the word overlap ratio between the Goal block and all supporting blocks to ensure every token serves the primary objective.
- **Completeness**: Verifies the presence of necessary structural components (e.g., heavily penalizing the absence of a defined Goal or Constraints).
- **Redundancy**: Utilizes Jaccard similarity to detect and penalize repetitive information across different blocks.
- **Clarity**: Evaluates sentence complexity (penalizing average sentence lengths over 25 words) and detects the excessive use of ambiguous pronouns ("it", "that", "those").

### 3. Prompt Generator
The generator compiles the active context blocks into a clean, markdown-structured system prompt. It clearly separates the permanent system context (Audience, Tech Stack, Output Style) from the temporary task context, ensuring the output is perfectly formatted for direct integration into tools like ChatGPT, Claude, or API requests.

## Technical Architecture

The application is designed with strict separation of concerns, ensuring that the core business logic remains framework-agnostic. 

- **Frontend Framework**: React with TanStack Start
- **Styling**: Tailwind CSS and Radix UI (Shadcn components)
- **State Management**: Zustand with `localStorage` persistence module
- **Core Engine**: Pure TypeScript logic (`scoring.ts` and `prompt-generator.ts`) completely decoupled from the DOM and React ecosystem, ensuring straightforward migration to alternative interfaces (such as a CLI) in the future.

## Local Development

The web application resides entirely within the `frontend` directory.

### Prerequisites
- Node.js (v20 or higher recommended)
- npm

### Installation

1. Clone the repository and navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install the project dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

4. Open your browser and navigate to the provided local address (typically `http://localhost:5173`).

## Project Structure

```text
frontend/
├── src/
│   ├── components/      # Reusable UI components (AppShell, Canvas, Optimizer)
│   ├── lib/
│   │   ├── prompt-generator.ts  # Logic for formatting the final markdown prompt
│   │   ├── scoring.ts           # Heuristic mathematical scoring engine
│   │   └── store.ts             # Zustand state management and persistence
│   └── routes/          # TanStack Start routing layer
```

## Context-Ly CLI: The Intelligence Layer

The true value of Context-Ly lies in its command-line interface, which transforms the tool from a simple prompt formatter into a persistent **Context Memory Layer** for your entire repository.

The CLI acts as a static analysis tool that discovers team conventions, evaluates repository complexity, and generates highly-optimized, token-efficient system prompts (`PROJECT_CONTEXT.md`) tailored to your exact stack.

### Setup

To begin using the CLI, activate the Python virtual environment located in the `cli` directory:

```bash
cd cli
.\venv\Scripts\activate
```

### Commands

#### 1. `contextly init`
Initializes Context-as-Code in the current directory. It creates a `.contextly` configuration folder and sets up your environment.

#### 2. `contextly analyze`
The ultimate context generator. This command automatically:
- Reads your `README.md`.
- Scans your entire project tree to build an ASCII architecture map.
- Inspects your dependencies to determine your language and framework (e.g. TypeScript, React).
- Pulls in both manually saved rules and statically inferred conventions.
- Merges everything into a massive, LLM-ready system prompt named `PROJECT_CONTEXT.md`.

#### 3. `contextly discover`
Runs the Pattern Discovery Engine. It statically analyzes the codebase using dependency heuristics and file-tree structures to figure out your team's unwritten conventions (e.g. "Uses Zustand", "Uses TailwindCSS", "Service Layer Hint").

#### 4. `contextly learn --auto`
The interactive gatekeeper to the True Memory Engine. It triggers the Discovery Engine and interactively asks if you want to save the discovered conventions:
```text
Save convention: TailwindCSS (Uses TailwindCSS for styling.)? [y/N]
```
Confirmed conventions are saved permanently to `.contextly/memory/rules.yaml`.

#### 5. `contextly memory`
Trust requires visibility. Use this command to inspect all rules and conventions that have been permanently saved to the project's memory.

#### 6. `contextly pack <dir>`
Bundles a specific directory (e.g., `src/components`) into an LLM-ready Context Pack. It reads all files, counts their tokens, and bundles them into `.contextly/packs/` so you can effortlessly copy-paste large portions of your codebase into an LLM without clutter.

#### 7. `contextly inspect`
Performs a deep-dive analysis on your repository complexity, warning you about excessively large files that will act as "Token Hogs" and consume too much context window.

---

## Changelog

### [0.1.2] - 2024-06-12

#### Added
- **Comprehensive Test Suite**: Introduced domain-specific test suites (`test_analyze.py`, `test_discover.py`, `test_export.py`, etc.) ensuring 100% test coverage across all CLI orchestration, generator, and core memory engine components.
- **Enhanced Data Validation**: Implemented strict default factories in Pydantic models (`RepositoryIntelligence`, `ProjectMemory`) to prevent mutable-default state mutations during context processing.

#### Changed
- **Architectural Decoupling**: Deprecated monolithic command testing structures in favor of isolated, modular test boundaries for all core system components.
- **Initialization Workflow**: The `contextly init` command now strictly generates configuration states in `.contextly/config.yaml`, formally deprecating the legacy `PROJECT_CONTEXT.md` initialization artifact requirement.

#### Fixed
- **Dependency Masking**: Resolved a heuristic bug in `FrameworkScanner` where concurrent backend frameworks (e.g., Django and FastAPI) would overwrite internal detection states.
- **Exception Taxonomy**: Standardized the internal error hierarchy (`ContextlyError`, `ValidationError`, `ScannerError`) to guarantee deterministic CLI failure reporting and graceful exit codes.

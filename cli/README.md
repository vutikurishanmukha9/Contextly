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

## Installation

You can install Context-Ly directly from PyPI:

```bash
pip install contextly
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

For all release notes and version history, please see the [CHANGELOG.md](CHANGELOG.md).

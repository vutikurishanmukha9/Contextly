# Context-Ly

Context-Ly is a context-engineering workspace designed to help developers and users construct highly optimized, token-efficient prompts for Large Language Models (LLMs). By organizing intent, background information, and constraints before generating a prompt, Context-Ly ensures that AI models receive maximum signal and minimum noise, resulting in sharper and more accurate responses.

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

## Future Roadmap: The Context Layer

The core libraries (`scoring.ts` and `prompt-generator.ts`) have been deliberately constructed as pure TypeScript modules to serve as the foundation for our ultimate goal: **The Context Layer**. 

While formatting prompts is useful, the true value of Context-Ly lies in **Context Intelligence**. The next major milestone is a powerful Command Line Interface (CLI) designed not just to format text, but to *understand* repositories.

### Upcoming CLI Features
- **`contextly analyze`**: The first moment of magic. Instead of manually adding files, the CLI will automatically scan a repository to detect the framework, database layer, architecture, and core business rules, automatically building a smart context map without overwhelming the LLM token limits.
- **Context Packs**: The ability to export highly compressed, reusable, and model-agnostic packages (e.g., `Architecture Pack`, `API Pack`).
- **`contextly learn`**: Building persistent **Context Memory**. The CLI will accumulate team conventions, coding patterns, and architectural decisions over time, transforming Context-Ly from a prompt generator into an organizational memory layer.

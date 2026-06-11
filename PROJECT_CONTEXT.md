# Project Context Intelligence

## Overview
# Context-Ly

Context-Ly is a context-engineering workspace designed to help developers and users construct highly optimized, token-efficient prompts for Large Language Models (LLMs). By organizing intent, background information, and constraints before generating a prompt, Context-Ly ensures that AI models receive maximum signal and minimum noise, resulting in sharper and more accurate responses.

## Overview

Modern AI applications often suffer from "token waste" - providing either too little context (requiring repeated clarifications) or too much irrelevant context (diluting the model's focus). Context-Ly solves this by introducing a structured methodology for building context packs. 

The application sits between the user's raw thoughts and the AI model, enforcing best practices in prompt engineering through an intuitive interface and a real-time heuristic scoring engine.

## Core Features

### 1. Context Builder
The Context Builder allows users to break down their prompts into dist...
[truncated]

## Team Conventions

### Explicit Rules
_(source: memory)_

**State Management**
- Uses Zustand for state management.
**Styling**
- Uses TailwindCSS for styling.
**Architecture Hints**
- Found UI components directory structure.

## Architecture Map
```text
Contextly/
├── cli/
│   ├── contextly/
│   │   ├── commands/
│   │   ├── generators/
│   │   ├── scanners/
│   │   ├── types/
│   │   ├── utils/
│   ├── contextly.egg-info/
├── frontend/
│   ├── .tanstack/
│   │   └── tmp/
│   ├── src/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── lib/
│   │   ├── routes/
├── PROJECT_CONTEXT.md
└── README.md
```

## Stack Identity
- **Primary Language**: TypeScript
- **Frontend Framework**: React (SPA)
- **Backend/Tooling**: None detected

## Dependency Weight
- **NPM Packages**: 69
- **Python Packages**: 0

*Generated automatically by Context-Ly (Max Level Architecture).*

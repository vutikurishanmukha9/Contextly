# Project Context Intelligence

## Overview
# Context-Ly

**Imagine trying to hire a new employee, but instead of giving them an employee handbook, a map of the office, and a list of company rules, you just dump 10,000 loose papers on their desk and say, "figure it out."** 

That is how most people use AI today. They dump raw files into ChatGPT or Claude and hope for the best. The AI gets confused, makes mistakes, and wastes time.

**Context-Ly fixes this.** 

Context-Ly is a tool that automatically reads your project, figures out your unwritten rules, maps out how everything is connected, and packages it perfectly for AI. When you use Context-Ly, the AI instantly understands your project exactly like a senior engineer would—saving you hours of typing, explaining, and correcting.

---

## Overview

Modern AI applications often suffer from "token waste" - providing either too little context (requiring repeated clarifications) or too much irrelevant context (diluting the model's focus). Context-Ly solves this by introducing a stru...
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
├── frontend/
│   ├── .tanstack/
│   │   └── tmp/
│   ├── src/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── routes/
├── .gitignore
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

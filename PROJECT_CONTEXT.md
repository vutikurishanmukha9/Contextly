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

### Explicit Rules (Memory)
- [State Management] Uses Zustand for state management. [High confidence]
- [Styling] Uses TailwindCSS for styling. [High confidence]
- [Data Validation] Uses Pydantic for data validation and parsing. [High confidence]
- [Testing] Uses Pytest for unit testing. [High confidence]
- [CLI Framework] Uses Typer for building CLI applications. [High confidence]
- [CLI Framework] Uses Rich for terminal formatting and output. [High confidence]
- [Frontend Framework] Uses React for building user interfaces. [High confidence]
- [Build Tool] Uses Vite as the frontend build tool. [High confidence]
- [Language] Uses TypeScript for type-safe JavaScript. [High confidence]
- [Architecture Hints] Found directory structure indicating Route-Based Architecture. [Medium confidence]
- [Architecture Hints] Found directory structure indicating Command Pattern. [Medium confidence]
- [Architecture Hints] Found directory structure indicating Utility Module. [Medium confidence]
- [Architecture Hints] Found directory structure indicating Test Suite. [Medium confidence]
- [Architecture Hints] Found directory structure indicating Scanner/Plugin Architecture. [Medium confidence]
- [Architecture Hints] Found directory structure indicating Generator Pattern. [Medium confidence]
- [Architecture Hints] Found directory structure indicating Core Module Architecture. [Medium confidence]
- [Architecture Hints] Found UI components directory structure. [Medium confidence]


## Architecture Map
````text
Contextly/
├── .github/
│   └── workflows/
│       ├── publish.yml
│       └── test.yml
├── cli/
│   ├── contextly/
│   │   ├── commands/
│   │   ├── core/
│   │   ├── generators/
│   │   ├── scanners/
│   │   ├── types/
│   │   ├── utils/
│   │   ├── __init__.py
│   │   ├── __main__.py
│   │   └── main.py
│   ├── contextly-1.0.3/
│   │   └── tests/
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── test_analyze.py
│   │   ├── test_cluster.py
│   │   ├── test_compression.py
│   │   ├── test_core.py
│   │   ├── test_discover.py
│   │   ├── test_explain_cmd.py
│   │   ├── test_explainer.py
│   │   ├── test_export.py
│   │   ├── test_fs.py
│   │   ├── test_generators.py
│   │   ├── test_graph.py
│   │   ├── test_init.py
│   │   ├── test_inspect.py
│   │   ├── test_learn.py
│   │   ├── test_memory.py
│   │   ├── test_pack.py
│   │   ├── test_ranking.py
│   │   ├── test_scanner_base.py
│   │   ├── test_scanner_dependencies.py
│   │   ├── test_scanner_framework.py
│   │   ├── test_scanner_language.py
│   │   └── test_scanner_patterns.py
│   ├── CHANGELOG.md
│   ├── README.md
│   └── pyproject.toml
├── frontend/
│   ├── .tanstack/
│   │   └── tmp/
│   ├── src/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── routes/
│   │   ├── main.tsx
│   │   ├── routeTree.gen.ts
│   │   ├── router.tsx
│   │   ├── server.ts
│   │   ├── start.ts
│   │   └── styles.css
│   ├── .gitignore
│   ├── .prettierignore
│   ├── .prettierrc
│   ├── bunfig.toml
│   ├── components.json
│   ├── eslint.config.js
│   ├── index.html
│   ├── package-lock.json
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
├── .gitignore
├── PROJECT_CONTEXT.md
└── README.md
````

## Stack Identity
```json
{
  "primary_language": "Python",
  "frontend_framework": "React (SPA)",
  "backend_tooling": "Python CLI"
}
```

## Dependency Weight
- **NPM Packages**: 69
- **Python Packages**: 12

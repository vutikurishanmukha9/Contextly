# Project Context Intelligence

## README Excerpt
# Context-Ly CLI

Context-Ly CLI is a proprietary Context Intelligence Engine designed to help developers generate high-quality, token-efficient context for Large Language Models (LLMs).

Rather than manually explaining your project to an AI assistant in every session, Context-Ly analyzes your repository, discovers conventions, learns team rules, and generates structured context files that help AI tools understand your codebase more effectively.

The CLI acts as a persistent Context Memory Layer for your repository, enabling consistent AI interactions across development workflows.

## Features

* Repository analysis and context generation
* Automatic framework and dependency detection
* Architecture visualization through project structure analysis
* Team convention discovery and memory management
* Persistent project-specific context storage
* LLM-ready Context Pack generation
* Repository complexity and token usage inspection
* Context-as-Code workflow with version-controlled project ...
[truncated]

## Team Conventions

### Explicit Rules (Memory)
- [Styling] Uses TailwindCSS for styling. [High confidence]
- [Data Validation] Uses Pydantic for data validation and parsing. [High confidence]
- [Testing] Uses Pytest for unit testing. [High confidence]
- [CLI Framework] Uses Typer for building CLI applications. [High confidence]
- [CLI Framework] Uses Rich for terminal formatting and output. [High confidence]
- [Frontend Framework] Uses React for building user interfaces. [High confidence]
- [Build Tool] Uses Vite as the frontend build tool. [High confidence]
- [Language] Uses TypeScript for type-safe JavaScript. [High confidence]
- [Architecture Hints] Found directory structure indicating Generator Pattern. [Medium confidence]
- [Architecture Hints] Found directory structure indicating Route-Based Architecture. [Medium confidence]
- [Architecture Hints] Found directory structure indicating Scanner/Plugin Architecture. [Medium confidence]
- [Architecture Hints] Found directory structure indicating Command Pattern. [Medium confidence]
- [Architecture Hints] Found directory structure indicating Utility Module. [Medium confidence]
- [Architecture Hints] Found directory structure indicating Test Suite. [Medium confidence]
- [Architecture Hints] Found directory structure indicating Core Module Architecture. [Medium confidence]
- [Architecture Hints] Found UI components directory structure. [Medium confidence]


## Architecture Map
````text
Contextly/
|-- .github/
|   `-- workflows/
|       |-- frontend-ci.yml
|       |-- publish.yml
|       `-- test.yml
|-- cli/
|   |-- contextly/
|   |   |-- commands/
|   |   |   |-- __init__.py
|   |   |   |-- analyze.py
|   |   |   |-- discover.py
|   |   |   |-- explain.py
|   |   |   |-- export.py
|   |   |   |-- impact.py
|   |   |   |-- init.py
|   |   |   |-- inspect.py
|   |   |   |-- learn.py
|   |   |   |-- memory.py
|   |   |   |-- pack.py
|   |   |   |-- stats.py
|   |   |   `-- summary.py
|   |   |-- core/
|   |   |   |-- analyzer/
|   |   |   |   |-- __init__.py
|   |   |   |   `-- engine.py
|   |   |   |-- discovery/
|   |   |   |   |-- rules/
|   |   |   |   |   `-- ... (truncated)
|   |   |   |   |-- __init__.py
|   |   |   |   |-- engine.py
|   |   |   |   `-- registry.py
|   |   |   |-- explainer/
|   |   |   |   `-- engine.py
|   |   |   |-- exporter/
|   |   |   |   |-- __init__.py
|   |   |   |   `-- engine.py
|   |   |   |-- graph/
|   |   |   |   |-- parsers/
|   |   |   |   |   `-- ... (truncated)
|   |   |   |   |-- assembler.py
|   |   |   |   |-- builder.py
|   |   |   |   |-- cluster.py
|   |   |   |   `-- validator.py
|   |   |   |-- impact/
|   |   |   |   `-- engine.py
|   |   |   |-- initializer/
|   |   |   |   |-- __init__.py
|   |   |   |   `-- engine.py
|   |   |   |-- inspector/
|   |   |   |   |-- __init__.py
|   |   |   |   `-- engine.py
|   |   |   |-- learner/
|   |   |   |   |-- __init__.py
|   |   |   |   `-- engine.py
|   |   |   |-- memory/
|   |   |   |   |-- __init__.py
|   |   |   |   `-- engine.py
|   |   |   |-- metrics/
|   |   |   |   |-- __init__.py
|   |   |   |   |-- base.py
|   |   |   |   `-- providers.py
|   |   |   |-- packer/
|   |   |   |   |-- __init__.py
|   |   |   |   |-- compression.py
|   |   |   |   |-- engine.py
|   |   |   |   |-- formatter.py
|   |   |   |   |-- ranking.py
|   |   |   |   `-- relevance.py
|   |   |   |-- __init__.py
|   |   |   `-- diagnostics.py
|   |   |-- generators/
|   |   |   |-- __init__.py
|   |   |   |-- base.py
|   |   |   |-- chatgpt.py
|   |   |   |-- claude.py
|   |   |   `-- registry.py
|   |   |-- scanners/
|   |   |   |-- __init__.py
|   |   |   |-- architecture.py
|   |   |   |-- base.py
|   |   |   |-- capabilities.py
|   |   |   |-- dependencies.py
|   |   |   |-- framework.py
|   |   |   |-- language.py
|   |   |   |-- patterns.py
|   |   |   `-- registry.py
|   |   |-- types/
|   |   |   |-- __init__.py
|   |   |   `-- models.py
|   |   |-- utils/
|   |   |   |-- __init__.py
|   |   |   |-- config.py
|   |   |   |-- console.py
|   |   |   |-- constants.py
|   |   |   |-- exceptions.py
|   |   |   |-- fs.py
|   |   |   |-- ignore.py
|   |   |   |-- io.py
|   |   |   |-- paths.py
|   |   |   |-- validation.py
|   |   |   `-- walker.py
|   |   |-- __init__.py
|   |   |-- __main__.py
|   |   `-- main.py
|   |-- tests/
|   |   |-- conftest.py
|   |   |-- test_analyze.py
|   |   |-- test_cluster.py
|   |   |-- test_compression.py
|   |   |-- test_core.py
|   |   |-- test_coverage_gap.py
|   |   |-- test_coverage_gap2.py
|   |   |-- test_coverage_gap_3.py
|   |   |-- test_coverage_gap_4.py
|   |   |-- test_coverage_gap_5.py
|   |   |-- test_coverage_main.py
|   |   |-- test_discover.py
|   |   |-- test_explain_cmd.py
|   |   |-- test_explainer.py
|   |   |-- test_export.py
|   |   |-- test_formatter.py
|   |   |-- test_fs.py
|   |   |-- test_fs_paths.py
|   |   |-- test_generators.py
|   |   |-- test_graph.py
|   |   |-- test_graph_extended.py
|   |   |-- test_impact.py
|   |   |-- test_impact_export_coverage.py
|   |   |-- test_init.py
|   |   |-- test_inspect.py
|   |   |-- test_learn.py
|   |   |-- test_main_coverage.py
|   |   |-- test_memory.py
|   |   |-- test_pack.py
|   |   |-- test_packer_engine_edge_cases.py
|   |   |-- test_packer_streaming.py
|   |   |-- test_python_parser_exhaustive.py
|   |   |-- test_qa_coverage.py
|   |   |-- test_qa_coverage_builder.py
|   |   |-- test_qa_coverage_memory.py
|   |   |-- test_qa_coverage_utils.py
|   |   |-- test_qa_remediation_part2.py
|   |   |-- test_qa_remediation_part4.py
|   |   |-- test_qa_remediation_part5.py
|   |   |-- test_qa_remediation_part6.py
|   |   |-- test_ranking.py
|   |   |-- test_ranking_edge_cases.py
|   |   |-- test_relevance.py
|   |   |-- test_scanner_base.py
|   |   |-- test_scanner_dependencies.py
|   |   |-- test_scanner_dependencies_exhaustive.py
|   |   |-- test_scanner_framework.py
|   |   |-- test_scanner_language.py
|   |   |-- test_scanner_patterns.py
|   |   |-- test_security_limits.py
|   |   `-- ... (3 more items)
|   |-- CHANGELOG.md
|   |-- pyproject.toml
|   |-- README.md
|   `-- uv.lock
|-- frontend/
|   |-- src/
|   |   |-- components/
|   |   |   |-- app/
|   |   |   |   `-- AppShell.tsx
|   |   |   |-- site/
|   |   |   |   |-- Logo.tsx
|   |   |   |   |-- SiteFooter.tsx
|   |   |   |   `-- SiteHeader.tsx
|   |   |   `-- ui/
|   |   |       |-- accordion.tsx
|   |   |       |-- alert-dialog.tsx
|   |   |       |-- alert.tsx
|   |   |       |-- aspect-ratio.tsx
|   |   |       |-- avatar.tsx
|   |   |       |-- badge.tsx
|   |   |       |-- breadcrumb.tsx
|   |   |       |-- button.tsx
|   |   |       |-- calendar.tsx
|   |   |       |-- card.tsx
|   |   |       |-- carousel.tsx
|   |   |       |-- chart.tsx
|   |   |       |-- checkbox.tsx
|   |   |       |-- collapsible.tsx
|   |   |       |-- command.tsx
|   |   |       |-- context-menu.tsx
|   |   |       |-- dialog.tsx
|   |   |       |-- drawer.tsx
|   |   |       |-- dropdown-menu.tsx
|   |   |       |-- form.tsx
|   |   |       |-- hover-card.tsx
|   |   |       |-- input-otp.tsx
|   |   |       |-- input.tsx
|   |   |       |-- label.tsx
|   |   |       |-- menubar.tsx
|   |   |       |-- navigation-menu.tsx
|   |   |       |-- pagination.tsx
|   |   |       |-- popover.tsx
|   |   |       |-- progress.tsx
|   |   |       |-- radio-group.tsx
|   |   |       |-- resizable.tsx
|   |   |       |-- scroll-area.tsx
|   |   |       |-- select.tsx
|   |   |       |-- separator.tsx
|   |   |       |-- sheet.tsx
|   |   |       |-- sidebar.tsx
|   |   |       |-- skeleton.tsx
|   |   |       |-- slider.tsx
|   |   |       |-- sonner.tsx
|   |   |       |-- switch.tsx
|   |   |       |-- table.tsx
|   |   |       |-- tabs.tsx
|   |   |       |-- textarea.tsx
|   |   |       |-- toggle-group.tsx
|   |   |       |-- toggle.tsx
|   |   |       `-- tooltip.tsx
|   |   |-- hooks/
|   |   |   `-- use-mobile.tsx
|   |   |-- routes/
|   |   |   |-- __root.tsx
|   |   |   |-- index.tsx
|   |   |   `-- README.md
|   |   |-- App.test.tsx
|   |   |-- main.tsx
|   |   |-- router.tsx
|   |   |-- routeTree.gen.ts
|   |   `-- styles.css
|   |-- .gitignore
|   |-- .prettierignore
|   |-- .prettierrc
|   |-- bunfig.toml
|   |-- components.json
|   |-- eslint.config.js
|   |-- index.html
|   |-- package-lock.json
|   |-- package.json
|   |-- tsconfig.json
|   `-- vite.config.ts
|-- .contextlyignore
|-- .gitignore
|-- LICENSE
|-- PROJECT_CONTEXT.md
|-- README.md
`-- SECURITY.md
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
- **NPM Packages**: 71
- **Python Packages**: 15

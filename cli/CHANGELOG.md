# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

### [1.0.7] - 2026-06-20

#### Added
- **Analytics & Stats Command**: Added `contextly stats` command offering deep insights into project health, structure, and cyclomatic complexity using pluggable metric providers.

#### Fixed
- **Packer Engine Integrity**: Fixed a state-rollback truncation bug (`PACK-001`) that could silently discard bytes if an error occurred mid-pack stream.
- **Repository Path Traversal Security**: Hardened context generation paths against arbitrary symlink traversal outside of the root boundary (`SEC-001`).
- **File Output Security**: Pack outputs and crash logs are now strictly masked to `0o600` and `0o700` (`SEC-002`, `SEC-003`).
- **Stream Corruption**: Enforced binary-mode stream handling (`REL-001`) to prevent Windows text-translation corruptions during pack rollbacks.
- **Cache TOCTOU Mitigations**: Replaced full-byte hashing with high-performance metadata snapshots in the `AnalyzerEngine` (`ARCH-001`) to eliminate Time-Of-Check to Time-Of-Use cache race conditions.
- **Root Discovery Resilience**: Patched a legacy lookup path (`FS-002`) in `find_project_root` to correctly target `config.yaml`.

### [1.0.6] - 2026-06-16

#### Fixed
- Improved overall stability and determinism across core engines.
- Fixed edge-case bugs in AST parsing, graph generation, and memory deduplication.
- Removed dead code and unused assets from the frontend directory.

### [1.0.5] - 2026-06-14

#### Added
- **Domain Clustering Engine (`DomainClusterer`)**: The AST Knowledge Graph is now automatically segmented into coherent architectural domains (e.g., `core`, `shared`, `auth`), allowing component isolation without human intervention.
- **Context Fusion (`contextly export <pack_name>`)**: Added the new `export` command that seamlessly merges persistent project memory with targeted context packs, automatically copying the optimized result to your clipboard.
- **Direct Package Execution**: Added `__main__.py` to the CLI package, enabling execution directly via `python -m contextly`.

#### Changed
- **Offline Context Generation**: Context-Ly now operates entirely offline. Generating repository context no longer requires an API key or consumes LLM tokens, making the analysis process faster, more secure, and completely free.
- **Structural Context Payloads (`contextly explain <domain>`)**: Completely refactored the `explain` command to extract a highly focused structural JSON payload based on the AST graph rather than streaming LLM responses.
- **Clipboard-First Workflow**: All context generation commands now default to pushing outputs directly to the clipboard via `pyperclip`.
- **Streamlined Outputs**: Console output has been refined for improved clarity and readability.
- **Zero Token Waste**: Removed the internal `AIClient` and external API dependencies entirely.
- **Analyzer Engine Optimization**: Introduced a unified `RepoWalker` in the `AnalyzerEngine` to share a single filesystem traversal across all scanners, drastically reducing I/O and CPU overhead on large repositories.
- **Memory Deduplication**: Updated `MemoryRule` to utilize a deterministic `name` field for precise rule deduplication in `contextly learn`, preventing repetitive entries in generated context files.

#### Fixed
- **Packer Engine Slicing**: Fixed an index mapping bug in the `PackerEngine` file slicing logic when truncating the selection based on token limit overflow, ensuring files are excluded robustly.
- **Domain Clusterer Edge-cases**: Addressed directory collision bugs when boundary markers are identically named to domains.
- **Import Graph Deadlocks**: Added sequential fallback to `ImportGraphBuilder` when multiprocessing pool execution encounters platform-specific instantiation failures.
- **Dependency Parsing**: Resolved a regex parsing issue inside `_parse_pyproject_toml` ensuring `!=` constraint negations are properly normalized.

### [1.0.4] - 2026-06-13

#### Fixed
- **Discovery Engine Blindspot**: The `DependencyScanner` and `PatternScanner` were using `.gitignore` rules during discovery, causing them to skip subdirectories like `frontend/` or `cli/` that users legitimately gitignore but still want Context-Ly to understand. Both scanners now use a lightweight, hardcoded skip-list (only truly toxic directories like `node_modules`, `.venv`, `.git`) decoupled from `.gitignore`.
- **Recursive Manifest Search**: The `DependencyScanner` previously only checked for `pyproject.toml` and `requirements.txt` at the project root. It now uses `os.walk` with depth-limited traversal (up to 3 levels) to find manifest files in subdirectories like `cli/pyproject.toml` or `frontend/package.json`.

#### Added
- **Expanded Pattern Recognition**: The `PatternScanner` now detects additional dependency-based patterns (`Typer`, `Rich`, `React`, `Vite`, `TypeScript`) and directory-based architectural hints (`scanners/`, `commands/`, `core/`, `utils/`, `tests/`, `routes/`, `generators/`).

### [1.0.3] - 2026-06-13

#### Fixed
- **Initialization Deadlock**: Resolved a paradoxical validation bug where running `contextly init` would prematurely abort if a partial/corrupted `.contextly` directory existed, while subsequent commands (`discover`, `learn`) would simultaneously fail due to the missing `config.yaml` file. 
- **State Recovery**: The `InitEngine` now specifically targets the presence of the `config.yaml` file rather than just the parent directory. It gracefully recovers partial states, rebuilds missing core directories (`memory/`, `packs/`), and successfully generates the configuration file using `exist_ok=True`.

### [1.0.2] - 2026-06-12

#### Fixed
- **Documentation Polish**: Standardized README Markdown hierarchy to display cleanly on PyPI, correcting inconsistent header sizes and fixing section structures.
- **Documentation**: Stripped out React/Frontend internal architecture details from the main CLI `README.md` to ensure the PyPI package page is strictly focused on the Python command-line interface.

### [1.0.0] - 2026-06-12

Initial stable release of Context-Ly on PyPI.

#### Added
- **Context Engineering**: Complete suite of CLI features including `analyze`, `pack`, `discover`, and `inspect` to seamlessly build LLM-ready context packs.
- **Project Initialization**: The `contextly init` command bootstraps the `.contextly` local directory and generates a clean `config.yaml`, providing a dedicated space for you to manually document and track your project's unwritten coding standards.

#### Changed
- **Enhanced Reliability & Performance**: The system guarantees deterministic execution, zero silent failures, and smooth handling of massive repository structures.

#### Fixed
- **Complex Framework Detection**: Precise detection for dual-backend or complex monorepo frameworks (e.g., projects utilizing both Django and FastAPI) without collisions.

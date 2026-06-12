# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

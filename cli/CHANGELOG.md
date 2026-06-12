# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

### [1.0.0] - 2024-06-12

Initial stable release of Context-Ly on PyPI.

#### Added
- **Context Engineering**: Complete suite of CLI features including `analyze`, `pack`, `discover`, and `inspect` to seamlessly build LLM-ready context packs.
- **Autonomous Initialization**: The `contextly init` command fully scaffolds and manages your workspace configurations automatically, eliminating the need to manually track initialization files.

#### Changed
- **Enhanced Reliability & Performance**: The system guarantees deterministic execution, zero silent failures, and smooth handling of massive repository structures.

#### Fixed
- **Complex Framework Detection**: Precise detection for dual-backend or complex monorepo frameworks (e.g., projects utilizing both Django and FastAPI) without collisions.

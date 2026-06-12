# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

### [0.1.2] - 2024-06-12

#### Added
- **Autonomous Initialization**: The `contextly init` command now fully scaffolds and manages your workspace configurations automatically, eliminating the need to manually track legacy initialization files.

#### Changed
- **Enhanced Reliability & Performance**: Significant stability improvements across all core commands. The system now guarantees deterministic execution, zero silent failures, and smoother handling of massive repository structures.

#### Fixed
- **Complex Framework Detection**: Resolved an issue where dual-backend or complex monorepo frameworks (e.g., projects utilizing both Django and FastAPI) could cause detection collisions. The framework intelligence engine is now significantly more precise.

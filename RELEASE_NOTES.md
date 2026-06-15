# Contextly v1.0.6 Release Notes

**Date:** June 15, 2026

Contextly v1.0.6 introduces critical stability, performance, and security improvements for enterprise scale usage.

## What's New

- **Security & Fault Tolerance:** Protected core AST parsing and packing engines against unreadable binary files to prevent memory leaks and crashes.
- **Cache Reliability:** Fixed Language Server state corruption issues by isolating discovery scans.
- **Language Parsing:** Improved TypeScript handling (including trailing commas and complex exports) to ensure accurate dependency resolution.
- **Performance:** Optimized filesystem traversal, reducing memory overhead, and implemented asynchronous parsing enhancements to bypass the Python GIL.
- **Determinism:** Ensured fully reproducible output ordering for improved LLM context caching.

This release ensures robust, scalable, and crash-free execution across all repositories.

import os
from pathlib import Path
from typing import Set, Optional, List
from .base import BaseScanner, ScannerError
from ..types.models import PatternScanResult, Pattern, DependencyScanResult
from ..utils.walker import RepoWalker
from ..utils.constants import is_skippable
class PatternScanner(BaseScanner):
    @property
    def name(self) -> str:
        return "Pattern Discovery Engine"

    def scan(self, root_dir: Path, dependencies: DependencyScanResult = None, file_paths: Optional[List[str]] = None, **kwargs) -> PatternScanResult:
        try:
            result = PatternScanResult()

            # 1. Dependency-Based Heuristics
            if dependencies:
                deps = set(dependencies.npm + dependencies.python)

                # State Management
                if "zustand" in deps:
                    result.patterns.append(Pattern(name="Zustand", category="State Management", confidence=1.0, description="Uses Zustand for state management."))
                elif "redux" in deps or "@reduxjs/toolkit" in deps:
                    result.patterns.append(Pattern(name="Redux", category="State Management", confidence=1.0, description="Uses Redux for state management."))
                elif "jotai" in deps:
                    result.patterns.append(Pattern(name="Jotai", category="State Management", confidence=1.0, description="Uses Jotai for state management."))

                # Styling
                if "tailwindcss" in deps:
                    result.patterns.append(Pattern(name="TailwindCSS", category="Styling", confidence=1.0, description="Uses TailwindCSS for styling."))
                elif "styled-components" in deps:
                    result.patterns.append(Pattern(name="Styled Components", category="Styling", confidence=1.0, description="Uses Styled Components for styling."))

                # Python Paradigms
                if "pydantic" in deps:
                    result.patterns.append(Pattern(name="Pydantic", category="Data Validation", confidence=1.0, description="Uses Pydantic for data validation and parsing."))
                if "pytest" in deps:
                    result.patterns.append(Pattern(name="Pytest", category="Testing", confidence=1.0, description="Uses Pytest for unit testing."))
                if "typer" in deps:
                    result.patterns.append(Pattern(name="Typer", category="CLI Framework", confidence=1.0, description="Uses Typer for building CLI applications."))
                if "rich" in deps:
                    result.patterns.append(Pattern(name="Rich", category="CLI Framework", confidence=1.0, description="Uses Rich for terminal formatting and output."))

                # Frontend Frameworks
                if "react" in deps:
                    result.patterns.append(Pattern(name="React", category="Frontend Framework", confidence=1.0, description="Uses React for building user interfaces."))
                if "vite" in deps:
                    result.patterns.append(Pattern(name="Vite", category="Build Tool", confidence=1.0, description="Uses Vite as the frontend build tool."))
                if "typescript" in deps:
                    result.patterns.append(Pattern(name="TypeScript", category="Language", confidence=1.0, description="Uses TypeScript for type-safe JavaScript."))

            # 2. File-Tree Based Heuristics using os.walk with pruning
            # 2. Structural Heuristics
            architectures: Set[str] = set()
            components_found = False

            # Extract directory names to check structural heuristics
            dirnames = set()
            components_found = False

            if file_paths is not None:
                for fp in file_paths:
                    parts = Path(fp).parts
                    for i in range(len(parts) - 1):
                        dirnames.add(parts[i])
            else:
                walker = RepoWalker(root_dir, max_depth=4, skip_predicate=is_skippable)
                try:
                    for _, subdirs, _ in walker.walk():
                        dirnames.update(subdirs)
                except OSError:
                    pass

            for dirname in dirnames:
                name = dirname.lower()
                if name == "services":
                    architectures.add("Service Layer")
                elif name == "repositories":
                    architectures.add("Repository Pattern")
                elif name in ("use_cases", "usecases"):
                    architectures.add("Clean Architecture (Use Cases)")
                elif name == "components":
                    components_found = True
                elif name == "scanners":
                    architectures.add("Scanner/Plugin Architecture")
                elif name == "commands":
                    architectures.add("Command Pattern")
                elif name == "core":
                    architectures.add("Core Module Architecture")
                elif name == "utils":
                    architectures.add("Utility Module")
                elif name == "tests":
                    architectures.add("Test Suite")
                elif name == "routes":
                    architectures.add("Route-Based Architecture")
                elif name == "generators":
                    architectures.add("Generator Pattern")

            for arch in architectures:
                result.patterns.append(Pattern(name=arch, category="Architecture Hints", confidence=0.8, description=f"Found directory structure indicating {arch}."))

            if components_found:
                result.patterns.append(Pattern(name="Component-Based UI", category="Architecture Hints", confidence=0.8, description="Found UI components directory structure."))

            return result
        except Exception as e:
            raise ScannerError(f"Pattern scan failed: {str(e)}")

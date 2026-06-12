from pathlib import Path
from typing import Set
from .base import BaseScanner, ScannerError
from ..types.models import PatternScanResult, Pattern, DependencyScanResult
from ..utils.ignore import IgnoreEngine

class PatternScanner(BaseScanner):
    @property
    def name(self) -> str:
        return "Pattern Discovery Engine"

    def scan(self, root_dir: Path, dependencies: DependencyScanResult = None, **kwargs) -> PatternScanResult:
        try:
            result = PatternScanResult()
            ignorer = IgnoreEngine(root_dir)
            
            # 1. Dependency-Based Heuristics
            if dependencies:
                deps = set(dependencies.npm + dependencies.python)
                
                # State Management
                if "zustand" in deps:
                    result.patterns.append(Pattern(name="Zustand", category="State Management", confidence="High", description="Uses Zustand for state management."))
                elif "redux" in deps or "@reduxjs/toolkit" in deps:
                    result.patterns.append(Pattern(name="Redux", category="State Management", confidence="High", description="Uses Redux for state management."))
                elif "jotai" in deps:
                    result.patterns.append(Pattern(name="Jotai", category="State Management", confidence="High", description="Uses Jotai for state management."))
                    
                # Styling
                if "tailwindcss" in deps:
                    result.patterns.append(Pattern(name="TailwindCSS", category="Styling", confidence="High", description="Uses TailwindCSS for styling."))
                elif "styled-components" in deps:
                    result.patterns.append(Pattern(name="Styled Components", category="Styling", confidence="High", description="Uses Styled Components for styling."))
                    
                # Python Paradigms
                if "pydantic" in deps:
                    result.patterns.append(Pattern(name="Pydantic", category="Data Validation", confidence="High", description="Uses Pydantic for data validation and parsing."))
                if "pytest" in deps:
                    result.patterns.append(Pattern(name="Pytest", category="Testing", confidence="High", description="Uses Pytest for unit testing."))

            # 2. File-Tree Based Heuristics
            architectures: Set[str] = set()
            components_found = False
            
            # We only do a shallow walk for directories to save time
            def _scan_dirs(dir_path: Path, depth: int = 0):
                if depth > 3:
                    return
                if not dir_path.is_dir():
                    return
                try:
                    entries = list(dir_path.iterdir())
                except PermissionError:
                    return
                for item in entries:
                    if item.is_dir() and not ignorer.is_ignored(item):
                        name = item.name.lower()
                        if name == "services":
                            architectures.add("Service Layer")
                        elif name == "repositories":
                            architectures.add("Repository Pattern")
                        elif name == "use_cases" or name == "usecases":
                            architectures.add("Clean Architecture (Use Cases)")
                        elif name == "components":
                            nonlocal components_found
                            components_found = True
                        _scan_dirs(item, depth + 1)
                        
            _scan_dirs(root_dir)
            
            for arch in architectures:
                result.patterns.append(Pattern(name=arch, category="Architecture Hints", confidence="Medium", description=f"Found directory structure indicating {arch}."))
                
            if components_found:
                result.patterns.append(Pattern(name="Component-Based UI", category="Architecture Hints", confidence="Medium", description="Found UI components directory structure."))
                
            return result
        except Exception as e:
            raise ScannerError(f"Pattern scan failed: {str(e)}")

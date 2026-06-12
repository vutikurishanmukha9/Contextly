from pathlib import Path
from typing import List

from ...scanners.dependencies import DependencyScanner
from ...scanners.patterns import PatternScanner
from ...types.models import PatternScanResult

class DiscoveryEngine:
    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        
    def discover(self) -> PatternScanResult:
        """
        Runs dependency and pattern scanners to discover conventions.
        """
        dep_scanner = DependencyScanner()
        pat_scanner = PatternScanner()
        
        deps_result = dep_scanner.scan(self.root_dir)
        patterns_result = pat_scanner.scan(self.root_dir, dependencies=deps_result)
        
        return patterns_result

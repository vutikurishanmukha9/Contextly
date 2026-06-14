import os
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional

from .rules.base import BaseRule
from ...types.models import Discovery, RepositoryCapability, PatternScanResult
from ...utils.walker import RepoWalker

class DiscoveryEngine:
    """
    Enterprise-grade engine for evaluating arbitrary Discovery Rules against a codebase.
    Decouples the file system traversal from the heuristic logic.
    """
    
    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self._paths_cache: List[str] = []
        self._is_loaded = False
        
        self._ALWAYS_SKIP = {
            ".git", "node_modules", "venv", ".venv", "__pycache__",
            ".contextly", "dist", "build", ".next", ".tox", ".eggs"
        }

    def discover(self) -> PatternScanResult:
        """
        Runs dependency and pattern scanners to discover conventions.
        Legacy method for Context-Ly learn/discover commands.
        """
        from ...scanners.dependencies import DependencyScanner
        from ...scanners.patterns import PatternScanner
        
        dep_scanner = DependencyScanner()
        pat_scanner = PatternScanner()
        
        deps_result = dep_scanner.scan(self.root_dir)
        patterns_result = pat_scanner.scan(self.root_dir, dependencies=deps_result)
        
        return patterns_result

    def _load_paths(self, file_paths: Optional[List[str]] = None):
        """
        Walks the repository once and caches relative paths in memory for O(1) rule evaluation.
        Can optionally accept a pre-computed list of files to avoid hitting the disk.
        """
        if self._is_loaded:
            return

        if file_paths is not None:
            # We want unique paths
            seen = set()
            for rel_path in file_paths:
                full_rel = rel_path
                if full_rel not in seen:
                    self._paths_cache.append(full_rel)
                    seen.add(full_rel)
                
                parts = Path(full_rel).parts
                for i in range(len(parts)):
                    partial = "/".join(parts[:i+1])
                    if partial not in seen:
                        self._paths_cache.append(partial)
                        seen.add(partial)
            self._is_loaded = True
            return

        def skip_predicate(path: Path) -> bool:
            name = path.name.lower()
            return name in self._ALWAYS_SKIP or name.endswith(".egg-info")

        walker = RepoWalker(self.root_dir, max_depth=4, skip_predicate=skip_predicate)

        for dirpath, dirnames, filenames in walker.walk():
            rel_path = str(Path(dirpath).relative_to(self.root_dir))
            
            # Add directories
            for dirname in dirnames:
                full_rel = os.path.join(rel_path, dirname).replace("\\", "/")
                if full_rel.startswith("./"):
                    full_rel = full_rel[2:]
                self._paths_cache.append(full_rel)
                
            # Add files
            for filename in filenames:
                full_rel = os.path.join(rel_path, filename).replace("\\", "/")
                if full_rel.startswith("./"):
                    full_rel = full_rel[2:]
                self._paths_cache.append(full_rel)

        self._is_loaded = True

    def evaluate_registry(
        self, 
        registry: Dict[str, List[BaseRule]], 
        discovery_class: type = Discovery,
        source_name: str = "DiscoveryEngine",
        file_paths: Optional[List[str]] = None
    ) -> List[any]:
        """
        Evaluates a dictionary mapping names to rulesets.
        
        Args:
            registry: Dict of "Target Name" -> [Rules]
            discovery_class: Pydantic model to construct (Discovery or RepositoryCapability)
            source_name: Tag for provenance auditing
            file_paths: Optional list of file paths to restrict evaluation
            
        Returns:
            List of constructed discovery_class instances.
        """
        self._load_paths(file_paths)
        results = []

        for target_name, rules in registry.items():
            total_score = 0.0
            all_evidence: Set[str] = set()

            for rule in rules:
                result = rule.evaluate(self._paths_cache)
                total_score += result.score_delta
                all_evidence.update(result.matched_evidence)

            if total_score > 0:
                confidence = min(1.0, total_score)
                # Keep top 5 evidence to avoid giant JSON files
                limited_evidence = list(all_evidence)[:5]
                
                if discovery_class == RepositoryCapability:
                    results.append(RepositoryCapability(
                        capability=target_name,
                        confidence=confidence,
                        evidence=limited_evidence,
                        node_ids=[]
                    ))
                else:
                    results.append(Discovery(
                        name=target_name,
                        confidence=confidence,
                        evidence=limited_evidence,
                        generated_by=source_name
                    ))
                    
        # Sort by highest confidence
        results.sort(key=lambda x: x.confidence, reverse=True)
        return results
